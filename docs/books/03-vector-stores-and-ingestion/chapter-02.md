# День 3. Лаба: pgvector рядом с Chroma

## Результат

Папка `~/proj/ai-labs/day3-pgvector/`: PostgreSQL с pgvector в Docker на homelab, те же чанки и векторы, что вчера в Chroma, HNSW и полнотекстовый индексы, гибридный поиск одним SQL-запросом, изоляция tenant через row-level security и таблица `results.md` — Hit@k, MRR@5 и p50/p95 Chroma против pgvector на том же golden-наборе. Плюс план миграции web-agent с оценкой трудозатрат. Вчера ты доказал, что умеешь измерять поиск; сегодня — что умеешь выбирать и эксплуатировать хранилище.

## Карта лабы

```mermaid
flowchart LR
    CH["Chroma дня 2\nchunks_openai"] --> LD["load.ipynb\nэкспорт векторов"]
    LD --> PG["PostgreSQL 17\npgvector, порт 5433"]
    SCH["schema.sql\nvector + tsvector\nHNSW + GIN + RLS"] --> PG
    PG --> D["dense\n<=> cosine"]
    PG --> F["fts\ntsvector russian"]
    D --> H["hybrid RRF\nодин SQL"]
    F --> H
    G["golden.jsonl\nдня 2"] --> EV["eval_pg.ipynb"]
    D --> EV
    F --> EV
    H --> EV
    EV --> RES["results.md\nChroma vs pgvector"]
    PG --> RLS["rls_demo.sql\nдва tenant"]
    PG --> EXP["explain.sql\nseq scan vs HNSW"]

    style CH fill:#2d2d2d,color:#fff
    style G fill:#2d2d2d,color:#fff
    style SCH fill:#2d2d2d,color:#fff
    style LD fill:#1a5276,color:#fff
    style PG fill:#7d6608,color:#fff
    style D fill:#1a5276,color:#fff
    style F fill:#1a5276,color:#fff
    style H fill:#4a235a,color:#fff
    style EV fill:#1a5276,color:#fff
    style RES fill:#1e8449,color:#fff
    style RLS fill:#6e2f1a,color:#fff
    style EXP fill:#1a5276,color:#fff
```

## Подготовка

Нужны результаты дня 2: снимок `day2-rag-eval/.local/chunks_openai/` и `fixtures/golden.jsonl`. Готовые файлы установлены командой `python3 scripts/install_labs.py --dest ~/proj/ai-labs` из корня курса (существующие отличающиеся файлы не перезаписываются). Postgres поднимаем отдельным контейнером на нестандартном порту, чтобы не задеть другие базы на машине.

```bash
cd ~/proj/ai-labs && source .venv/bin/activate && source .env
mkdir -p day3-pgvector && cd day3-pgvector
```

## Шаг 1. PostgreSQL с pgvector в Docker (5 минут)

Секреты для этой учебной базы генерируются **один раз**, кладутся в `~/proj/ai-labs/.env` и дальше просто
подхватываются: и `docker compose` (он сам читает `.env` рядом с `docker-compose.yml`), и Python-скрипты
(через `labkit`, как ключ OpenRouter в дне 1). Ничего не экспортировать заново в новой сессии.

```yaml
# ~/proj/ai-labs/day3-pgvector/docker-compose.yml
services:
  pg:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_USER: rag_admin
      POSTGRES_PASSWORD: "${PG_ADMIN_PASSWORD:?set PG_ADMIN_PASSWORD}"
      POSTGRES_DB: rag
    ports:
      - "127.0.0.1:5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rag_admin -d rag"]
      interval: 2s
      timeout: 3s
      retries: 30
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

Один раз — сгенерировать и дописать в `~/proj/ai-labs/.env` (уже в `.gitignore`, `chmod 600` сохраняется):

```bash
{
  echo "export PG_ADMIN_PASSWORD=\"$(python -c 'import secrets; print(secrets.token_hex(24))')\""
  echo "export PG_APP_PASSWORD=\"$(python -c 'import secrets; print(secrets.token_hex(24))')\""
  echo 'export PG_ADMIN_DSN="postgresql://rag_admin:$PG_ADMIN_PASSWORD@127.0.0.1:5433/rag"'
  echo 'export PG_DSN="postgresql://rag_app:$PG_APP_PASSWORD@127.0.0.1:5433/rag"'
} >> ~/proj/ai-labs/.env
source ~/proj/ai-labs/.env
```

Дальше — в любой сессии, без повторной генерации:

```bash
docker compose up -d --wait
docker compose exec pg psql -U rag_admin -d rag -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extversion FROM pg_extension WHERE extname='vector';"
```

Команды рассчитаны на новую учебную БД. Существующий volume сохраняет старого пользователя и пароль: не удаляй его ради инструкции, используй отдельное имя Compose-проекта и свободный порт. `docker compose` сам читает `.env` из своей рабочей директории `day3-pgvector/` — но переменные там нет, они в `~/proj/ai-labs/.env` на уровень выше, поэтому их обязательно нужно `source` перед `docker compose up`, иначе сработает заглушка `:?set PG_ADMIN_PASSWORD` из compose-файла. Административный DSN нельзя использовать в приложении.

Ожидаемо версия расширения `0.8.x` или новее. Запиши её — итеративный скан из шага 5 требует не ниже 0.8.0.

## Шаг 2. Схема: вектор, полнотекст, индексы, RLS

```sql
-- ~/proj/ai-labs/day3-pgvector/schema.sql
\set ON_ERROR_STOP on
CREATE EXTENSION IF NOT EXISTS vector;
DO $roles$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rag_app') THEN
        CREATE ROLE rag_app LOGIN NOSUPERUSER NOBYPASSRLS;
    END IF;
END
$roles$;
ALTER ROLE rag_app WITH LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD :'app_password';
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO rag_app;
CREATE TABLE IF NOT EXISTS chunks (
    id          text PRIMARY KEY,
    tenant_id   int NOT NULL,
    filename    text NOT NULL,
    chunk_index int NOT NULL,
    text        text NOT NULL,
    embedding   vector(1536) NOT NULL,
    tsv         tsvector GENERATED ALWAYS AS (to_tsvector('russian', text)) STORED
);
CREATE TABLE IF NOT EXISTS lab_snapshot (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    config jsonb NOT NULL
);
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON chunks;
CREATE POLICY tenant_isolation ON chunks
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::int);
REVOKE ALL ON chunks, lab_snapshot FROM PUBLIC;
GRANT SELECT ON chunks, lab_snapshot TO rag_app;
```

```bash
docker compose exec -T pg psql -U rag_admin -d rag -v ON_ERROR_STOP=1 -v app_password="$PG_APP_PASSWORD" < schema.sql
```

Никогда не заданный GUC возвращает NULL, а после `RESET` — пустую строку. `NULLIF(..., '')` покрывает оба случая: нет tenant — нет строк. `FORCE` подчиняет политике владельца, но **не суперпользователя и не BYPASSRLS**. Все запросы приложения и тесты выполняются как `rag_app`. RLS защищает от забытого фильтра, но не от клиента с произвольным SQL: tenant устанавливает доверенный сервер после аутентификации, не модель и не пользователь запроса.

Основание: [PostgreSQL RLS](https://www.postgresql.org/docs/17/ddl-rowsecurity.html), [роль POSTGRES_USER в Docker](https://hub.docker.com/_/postgres).

## Шаг 3. Загрузка из Chroma

Векторы уже посчитаны вчера — платить за эмбеддинги второй раз не нужно. Разбиение на tenant 1 и 2 уже записано в снимке дня 2; переносим его без изменений. Схема лабы рассчитана на 1536 измерений; для иной модели нужна отдельная таблица с её размерностью, а не смешивание векторов.

```python
# ~/proj/ai-labs/day3-pgvector/load.py
# %% [markdown]
# # День 3 · перенос снимка из Chroma в Postgres
#
# Векторы уже посчитаны вчера — платить за эмбеддинги второй раз не нужно, `load.py` только копирует
# id, тексты и векторы в другое хранилище.
# %%
"""Копирует вчерашний снимок Chroma в Postgres: те же id, тексты и векторы, без пересчёта эмбеддингов."""
import labkit
labkit.use_day("day2-rag-eval")  # добавляет day2-rag-eval в sys.path — оттуда common.py
from common import load_config, snapshot_path

# --- НАСТРОЙКИ ---
COLLECTION = "chunks_openai"   # снимок из day2-rag-eval/index.py, который загружаем
REPLACE_LAB_DATA = False       # True — разрешить перезаписать уже загруженную учебную таблицу (не для прода!)

# %% [markdown]
# ## Читаем снимок обратно из Chroma
#
# Схема этой лабы жёстко рассчитана на 1536 измерений (`vector(1536)` в `schema.sql`) — размерность
# зафиксирована типом колонки, а не проверкой в коде на всякий случай. Другая модель эмбеддингов дала
# бы другую размерность — для неё нужна отдельная таблица, не смешивание векторов разных моделей в
# одной колонке (drill 2 в дне 7 разбирает это на реальной ошибке).
# %%
config = load_config(COLLECTION)
if config["dimension"] != 1536:
    raise SystemExit("эта учебная схема vector(1536); для другой модели нужна отдельная схема")
import chromadb
import numpy as np
col = chromadb.PersistentClient(path=str(snapshot_path(COLLECTION) / "chroma")).get_collection(COLLECTION)
data = col.get(include=["embeddings", "documents", "metadatas"])
rows = [(cid, m["tenant_id"], m["filename"], m["chunk_index"], doc, np.asarray(emb, dtype=np.float32))
        for cid, doc, m, emb in zip(data["ids"], data["documents"], data["metadatas"], data["embeddings"])]
if not rows:
    raise SystemExit("снимок пуст")
print(f"строк для загрузки: {len(rows)}")

# %% [markdown]
# ## Запись в Postgres — только от имени rag_admin
#
# `register_vector` учит psycopg сериализовать numpy-массив в тип `vector`. Роль подключения
# проверяется явно (`current_user == "rag_admin"`) — это административная роль с `BYPASSRLS`, ей и
# положено видеть и переписывать все строки при загрузке; обычные запросы приложения идут от `rag_app`
# и такого права не имеют (день 3, шаг 7). Замена данных — не `INSERT ... ON CONFLICT`, а `TRUNCATE` +
# вставка заново: для учебного снимка это проще и атомарнее, политика RLS при этом не отключается.
# %%
import psycopg
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb

with psycopg.connect(labkit.env("PG_ADMIN_DSN", required=True)) as conn:
    register_vector(conn)                                       # учит psycopg сериализовать numpy-вектор
    if conn.execute("SELECT current_database(), current_user").fetchone() != ("rag", "rag_admin"):
        raise RuntimeError("загрузчик разрешён только в учебной БД rag от rag_admin")
    if conn.execute("SELECT count(*) FROM chunks").fetchone()[0] and not REPLACE_LAB_DATA:
        raise RuntimeError("таблица непуста; проверь PG_ADMIN_DSN и явно поставь REPLACE_LAB_DATA = True")
    # Только учебный admin; атомарная замена снимка, политика RLS не отключается.
    conn.execute("TRUNCATE chunks, lab_snapshot")
    with conn.cursor() as cur:
        cur.executemany("INSERT INTO chunks (id, tenant_id, filename, chunk_index, text, embedding) VALUES (%s,%s,%s,%s,%s,%s)", rows)
    conn.execute("INSERT INTO lab_snapshot (config) VALUES (%s)", (Jsonb(config),))
    for tenant, count in conn.execute("SELECT tenant_id, count(*) FROM chunks GROUP BY tenant_id ORDER BY 1"):
        print(f"tenant {tenant}: чанков {count}")
print(f"загружен снимок {config['dataset_hash']}, строк {len(rows)}")
```

Запуск: открой `load.ipynb` в VS Code и нажми ▶ Run All. Политика не отключается: административная роль обходит её только при загрузке. Для повторной замены **учебной** таблицы нужен явный `REPLACE_LAB_DATA = True`; в проде применяй версионирование/backfill, а не TRUNCATE. Идентификаторы и tenant берутся из исходного снимка, поэтому сравнение остаётся сопоставимым.

## Шаг 4. Индексы и EXPLAIN: увидеть разницу

```sql
-- ~/proj/ai-labs/day3-pgvector/indexes.sql
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS chunks_tsv_gin ON chunks USING gin (tsv);
ANALYZE chunks;
```

```bash
docker compose exec -T pg psql -U rag_admin -d rag -v ON_ERROR_STOP=1 < indexes.sql
```

Индексы создаёт администратор после загрузки. EXPLAIN выполняет прикладная роль: сначала принудительный Seq Scan, затем HNSW. На нескольких сотнях строк планировщик выберет последовательный скан даже при наличии индекса — это правильно с его стороны; для демонстрации индекс включаем принудительно.

```sql
-- ~/proj/ai-labs/day3-pgvector/explain.sql
-- один вектор запроса берём прямо из таблицы, чтобы не тащить его из Python
SET app.tenant_id = '1';
SET enable_indexscan = off;
SET enable_bitmapscan = off;
\set qvec 'SELECT embedding FROM chunks WHERE tenant_id = 1 ORDER BY id LIMIT 1'

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, filename, 1 - (embedding <=> (:qvec)) AS score
FROM chunks ORDER BY embedding <=> (:qvec) LIMIT 5;

RESET enable_indexscan;
RESET enable_bitmapscan;

SET enable_seqscan = off;   -- только для демонстрации на малой таблице
SET hnsw.ef_search = 40;
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, filename, 1 - (embedding <=> (:qvec)) AS score
FROM chunks ORDER BY embedding <=> (:qvec) LIMIT 5;

-- ловушка фильтра: селективный фильтр после индекса возвращает меньше LIMIT
SET hnsw.iterative_scan = off;
SELECT count(*) AS rows_without_iterative FROM (
  SELECT id FROM chunks WHERE filename = (SELECT filename FROM chunks WHERE tenant_id = 1 ORDER BY id DESC LIMIT 1)
  ORDER BY embedding <=> (:qvec) LIMIT 5) t;

SET hnsw.iterative_scan = strict_order;
SELECT count(*) AS rows_with_iterative FROM (
  SELECT id FROM chunks WHERE filename = (SELECT filename FROM chunks WHERE tenant_id = 1 ORDER BY id DESC LIMIT 1)
  ORDER BY embedding <=> (:qvec) LIMIT 5) t;
RESET enable_seqscan;
```

```bash
docker compose exec -T -e PGPASSWORD="$PG_APP_PASSWORD" pg psql -h 127.0.0.1 -U rag_app -d rag -v ON_ERROR_STOP=1 < explain.sql
```

Что смотреть: в первом плане `Seq Scan` и `Sort`, во втором — `Index Scan using chunks_embedding_hnsw`; время выполнения обоих запиши. В двух последних запросах сравни число строк: без итеративного скана фильтр по одному файлу может дать меньше пяти строк, с ним строк может стать больше, но не больше числа подходящих чанков и лимитов обхода. На малом fixture эффект может отсутствовать: это корректный результат, а не причина подгонять эксперимент. Масштабируемость на четырёх документах не доказывается.

## Шаг 5. Три ретривера одним адаптером

```python
# ~/proj/ai-labs/day3-pgvector/pgstore.py
"""То же самое, что Store из дня 2 (dense/BM25/hybrid), но SQL-запросами к Postgres вместо Chroma."""
import labkit
labkit.use_day("day2-rag-eval")
from embed import Embedder

DENSE_SQL = """
SELECT id, tenant_id, filename, chunk_index, text, 1 - (embedding <=> %(v)s) AS score
FROM chunks ORDER BY embedding <=> %(v)s LIMIT %(k)s"""

FTS_SQL = """
SELECT id, tenant_id, filename, chunk_index, text, ts_rank_cd(tsv, q) AS score
FROM chunks, plainto_tsquery('russian', %(q)s) q
WHERE tsv @@ q ORDER BY score DESC LIMIT %(k)s"""

HYBRID_SQL = """
WITH dense AS (
    SELECT id, row_number() OVER (ORDER BY embedding <=> %(v)s) AS r
    FROM chunks ORDER BY embedding <=> %(v)s LIMIT %(cand)s
), fts AS (
    SELECT id, row_number() OVER (ORDER BY ts_rank_cd(tsv, q) DESC) AS r
    FROM chunks, plainto_tsquery('russian', %(q)s) q
    WHERE tsv @@ q ORDER BY ts_rank_cd(tsv, q) DESC LIMIT %(cand)s
)
SELECT c.id, c.tenant_id, c.filename, c.chunk_index, c.text,
       COALESCE(1.0 / (60 + dense.r), 0) + COALESCE(1.0 / (60 + fts.r), 0) AS score
FROM chunks c
LEFT JOIN dense ON dense.id = c.id
LEFT JOIN fts ON fts.id = c.id
WHERE dense.id IS NOT NULL OR fts.id IS NOT NULL
ORDER BY score DESC LIMIT %(k)s"""

class PgStore:
    """Подключение от имени rag_app (не admin!) — тогда работает RLS и tenant нельзя обойти."""

    def __init__(self, tenant_id: int, embedder: Embedder):
        if type(tenant_id) is not int or tenant_id <= 0:
            raise ValueError("tenant_id должен быть положительным int")
        import psycopg
        from pgvector.psycopg import register_vector
        self.conn = psycopg.connect(labkit.env("PG_DSN", required=True), autocommit=True)
        register_vector(self.conn)
        flags = self.conn.execute("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user").fetchone()
        if any(flags):
            self.conn.close()
            raise RuntimeError("PG_DSN приложения не может использовать SUPERUSER/BYPASSRLS")
        self.tenant_id, self.embedder = tenant_id, embedder

    def _rows(self, sql: str, params=None) -> list[dict]:
        """Каждый запрос — своя транзакция: tenant выставляется и автоматически сбрасывается вместе с ней."""
        with self.conn.transaction():
            self.conn.execute("SELECT set_config('app.tenant_id', %s, true)", (str(self.tenant_id),))
            self.conn.execute("SET LOCAL hnsw.ef_search = 100")
            self.conn.execute("SET LOCAL hnsw.iterative_scan = strict_order")
            cur = self.conn.execute(sql, params)
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def _vec(self, q: str):
        import numpy as np
        return np.asarray(self.embedder.embed_query(q), dtype=np.float32)

    def dense(self, q: str, k: int) -> list[dict]:
        return self._rows(DENSE_SQL, {"v": self._vec(q), "k": k})

    def fts(self, q: str, k: int) -> list[dict]:
        return self._rows(FTS_SQL, {"q": q, "k": k})

    def hybrid(self, q: str, k: int, cand: int = 20) -> list[dict]:
        return self._rows(HYBRID_SQL, {"v": self._vec(q), "q": q, "k": k, "cand": cand})

    def visible_rows(self) -> list[dict]:
        """Все строки, видимые этой ролью прямо сейчас — используется для сверки со снимком Chroma."""
        return self._rows("SELECT id, tenant_id, filename, chunk_index, text FROM chunks ORDER BY id")

    def snapshot_config(self) -> dict:
        return self._rows("SELECT config FROM lab_snapshot")[0]["config"]

    def close(self) -> None:
        self.conn.close()
```

В SQL поиска нет `WHERE tenant_id`: его добавляет RLS, но только для прикладной роли. `set_config(..., true)` устанавливает контекст **внутри каждой транзакции**, после выхода контекст сброшен; исключение тоже завершает транзакцию. Это безопаснее session SET для пула. Psycopg 3 не поддерживает параметры в SQL `SET`, поэтому здесь используется функция: [официальное объяснение server-side binding](https://www.psycopg.org/psycopg3/docs/basic/from_pg2.html#server-side-binding).

## Шаг 6. Оценка и сравнение с Chroma

Переиспользуем `evaluate` из вчерашнего `eval.py` — метрики и формат таблицы должны совпадать, чтобы сравнение было честным. Golden-набор и query-векторы общие. Для каждого tenant обе системы получают одинаковые документы, вопросы и фильтры; код сверяет снимок и видимые строки до измерения.

```python
# ~/proj/ai-labs/day3-pgvector/eval_pg.py
# %% [markdown]
# # День 3 · Chroma против pgvector на одном golden-наборе
#
# Переиспользуем ровно ту же функцию `evaluate` из дня 2 — метрики и формат таблицы должны совпадать,
# чтобы сравнение было честным: одна и та же линейка Hit@5/MRR@5 для обеих систем.
# %%
"""Тот же golden-набор и та же функция evaluate из дня 2 — только Postgres рядом с Chroma, честное сравнение."""
import time

import labkit
labkit.use_day("day2-rag-eval")
from common import golden_for_rows, load_config, load_golden, load_rows
from eval import evaluate

# --- НАСТРОЙКИ ---
COLLECTION = "chunks_openai"   # снимок, загруженный load.py
GOLDEN_PATH = None             # None — стандартный golden.jsonl

cfg, rows = load_config(COLLECTION), load_rows(COLLECTION)
golden = golden_for_rows(load_golden(GOLDEN_PATH), rows, require_all=True)
from embed import Embedder
from retrievers import Store
from pgstore import PgStore

embedder = Embedder(cfg["embedder"], cfg["model"])
t0 = time.perf_counter()
for g in golden:
    embedder.embed_query(g["q"])
print(f"query embeddings, вне поиска: {time.perf_counter() - t0:.2f} s")

# %% [markdown]
# ## По каждому tenant отдельно — и сверка, что снимки совпадают
#
# `pg.snapshot_config() != cfg` и сверка видимых строк (`actual != expected`) — не формальность: если
# кто-то загрузил в Postgres другой снимок, чем тот, что сейчас в Chroma, сравнение будет нечестным.
# Изоляция tenant видна прямо здесь: `PgStore(tenant, embedder)` подключается от `rag_app`, и
# `pg.visible_rows()` вернёт **только** строки своего tenant — это RLS в действии, ещё до шага 7,
# где ты проверишь то же самое явными негативными тестами.
# %%
print("| tenant | retriever | Hit@5 | MRR@5 | p50 ms | p95 ms |")
print("|---|---|---|---|---|---|")
for tenant in sorted({r["tenant_id"] for r in rows}):
    subset_rows = [r for r in rows if r["tenant_id"] == tenant]
    subset = golden_for_rows(golden, subset_rows)
    if not subset:
        continue
    chroma = Store(COLLECTION, embedder, tenant_id=tenant)
    pg = PgStore(tenant, embedder)
    try:
        if pg.snapshot_config() != cfg:
            raise RuntimeError("Postgres и Chroma содержат разные снимки; повтори контролируемую загрузку")
        actual = {r["id"]: r for r in pg.visible_rows()}
        expected = {r["id"]: r for r in subset_rows}
        if actual != expected:
            raise RuntimeError("разные документы/tenant: сравнение остановлено")
        for name, fn in (("Chroma dense", chroma.dense), ("pgvector dense", pg.dense),
                         ("Chroma BM25", chroma.bm25_search), ("Postgres FTS", pg.fts),
                         ("Chroma hybrid", chroma.hybrid), ("Postgres hybrid", pg.hybrid)):
            r = evaluate(name, fn, subset)
            print(f"| {tenant} ({len(subset)} q) | {name} | {r['recall@5']:.2f} | {r['mrr']:.2f} | {r['latency_ms']:.1f} | {r['p95_ms']:.1f} |")
    finally:
        pg.close()
```

Запуск: открой `eval_pg.ipynb` в VS Code и нажми ▶ Run All. Dense сравнивается на одинаковом подкорпусе. ANN-индексы могут давать разные попадания: сравни с exact baseline и параметрами обхода, не объявляй совпадение обязательным. Полнотекстовый поиск Postgres против вчерашнего BM25 со стеммингом — разные алгоритмы, разница ожидаема в обе стороны; запиши, какая.

## Шаг 7. RLS: доказать, что утечки нет

```sql
-- ~/proj/ai-labs/day3-pgvector/rls_demo.sql
\set ON_ERROR_STOP on
DO $check$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = current_user AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'тест должен выполняться прикладной ролью';
    END IF;
END
$check$;
SET app.tenant_id = '1';
SELECT tenant_id, count(*) FROM chunks GROUP BY tenant_id;
DO $check$
BEGIN
    IF NOT EXISTS (SELECT FROM chunks) OR EXISTS (SELECT FROM chunks WHERE tenant_id <> 1) THEN
        RAISE EXCEPTION 'изоляция tenant 1 не работает или данные не загружены';
    END IF;
END
$check$;
SET app.tenant_id = '2';
SELECT tenant_id, count(*) FROM chunks GROUP BY tenant_id;
DO $check$
BEGIN
    IF NOT EXISTS (SELECT FROM chunks) OR EXISTS (SELECT FROM chunks WHERE tenant_id <> 2) THEN
        RAISE EXCEPTION 'изоляция tenant 2 не работает или данные не загружены';
    END IF;
END
$check$;
RESET app.tenant_id;
SELECT count(*) AS visible_without_tenant FROM chunks;
DO $check$
BEGIN
    IF EXISTS (SELECT FROM chunks) THEN
        RAISE EXCEPTION 'RESET оставил доступ к данным';
    END IF;
END
$check$;
BEGIN;
SELECT set_config('app.tenant_id', '1', true);
SELECT count(*) AS leak_attempt FROM chunks WHERE tenant_id = 2;
DO $check$
BEGIN
    IF EXISTS (SELECT FROM chunks WHERE tenant_id = 2) THEN
        RAISE EXCEPTION 'обход фильтра';
    END IF;
END
$check$;
COMMIT;
DO $check$
BEGIN
    IF EXISTS (SELECT FROM chunks) THEN
        RAISE EXCEPTION 'tenant остался после транзакции';
    END IF;
END
$check$;
```

```bash
docker compose exec -T -e PGPASSWORD="$PG_APP_PASSWORD" pg psql -h 127.0.0.1 -U rag_app -d rag -v ON_ERROR_STOP=1 < rls_demo.sql
```

Четыре результата и успешные SQL-assertions — в отчёт. Дополнительно проверяется сброс контекста после транзакции, а не только RESET. Это ответ на вопрос «как гарантируете изоляцию», который можно показать, а не рассказать.

## Шаг 8. Парсинг с таблицами: Docling против pypdf (30 минут, по желанию)

Если в корпусе есть PDF с таблицей — сравни, что извлекают `pypdf` (как в web-agent) и Docling. Установка Docling тяжёлая (модели раскладки, сотни мегабайт), делай только при запасе времени.

```bash
# Docling — отдельное необязательное окружение и зафиксированная версия, не обновляй основное venv.
python -c "from docling.document_converter import DocumentConverter; import sys; print(DocumentConverter().convert(sys.argv[1]).document.export_to_markdown()[:3000])" corpus-sample.pdf
python -c "from pypdf import PdfReader; import sys; print((PdfReader(sys.argv[1]).pages[0].extract_text() or '')[:3000])" corpus-sample.pdf
```

Смотри на таблицу: у pypdf строки и колонки склеятся в поток слов, у Docling — Markdown-таблица. В отчёт: пример из трёх строк обоих вариантов и вывод, для каких документов web-agent стоило бы включить Docling как опцию, а для каких лёгкий парсер достаточен.

## Шаг 9. results.md: сравнение и план миграции

```markdown
# День 3 — pgvector рядом с Chroma (дата, pgvector x.y.z, чанков N)

## Качество и латентность (тот же golden-набор)
| tenant + хранилище | retriever | Hit@5 | MRR@5 | p50/p95, мс |
| Chroma (тот же tenant, текущий прогон) | dense | … | … | … |
| pgvector | dense | … | … | … |
| pgvector | fts (ts_rank_cd) | … | … | … |
| pgvector | hybrid RRF в SQL | … | … | … |

## EXPLAIN
- принудительный Seq Scan, … мс; с HNSW: Index Scan, … мс
- фильтр + LIMIT 5: без iterative_scan … строк, с strict_order … строк

## RLS
- tenant 1 видит …, tenant 2 видит …, без tenant 0, попытка WHERE tenant_id=2 → 0

## План миграции web-agent Chroma → pgvector
1. Таблица chunks в существующем Postgres web-agent (tenant_id = site_id), RLS, HNSW, GIN. Alembic-миграция.
2. Двойная запись в doc-parser: reindex пишет в Chroma и в Postgres (флаг). Backfill существующих коллекций скриптом.
3. retriever.py: режим dense | hybrid по настройке сайта; set_config(..., true) в транзакции каждого запроса, только от rag_app.
4. Сравнение на golden-наборе tenant ksm; переключение чтения на pgvector; неделя наблюдения; удаление Chroma из compose.
5. Оценка: … часов; риски: долгая сборка HNSW на большом tenant (строить CONCURRENTLY), размер БД (+ N ГБ), пул соединений и SET на сессии (PgBouncer в transaction mode требует SET LOCAL в транзакции).

## Выводы
```

Из `~/proj/ai-labs`: `git add day3-pgvector/*.py day3-pgvector/*.sql day3-pgvector/docker-compose.yml day3-pgvector/results.md`, затем `git diff --cached`. Проверь отсутствие DSN, паролей и приватного текста; после проверки — коммит и push.

## Если не получилось

- **`psycopg` не видит `vector`** — забыт `register_vector(conn)` после подключения; без него numpy-массив не сериализуется.
- **`current_setting` падает `unrecognized configuration parameter`** — используй двухсоставное имя `app.tenant_id` (с точкой) и `current_setting('app.tenant_id', true)`.
- **Все запросы возвращают 0 строк** — проверь прикладную роль, загруженный tenant и вызов set_config внутри той же транзакции. Не заменяй PG_DSN административным ради появления строк.
- **Индекс не используется в EXPLAIN** — таблица мала; `SET enable_seqscan = off` только для демонстрации; на проде планировщик переключится сам с ростом.
- **`iterative_scan` — unrecognized** — pgvector ниже 0.8; обнови образ `pgvector/pgvector:pg17`.
- **Полнотекст не находит очевидное** — конфигурация `russian` должна стоять и в `to_tsvector`, и в `plainto_tsquery`; проверь `SELECT to_tsvector('russian', 'абонементы')`.
- **Docling ставится вечно** — это нормально, отложи в stretch; лаба засчитывается без шага 8.

## Практика

1. **Qdrant за 20 минут**: `docker run -d -p 127.0.0.1:6333:6333 qdrant/qdrant`, клиент из зафиксированного окружения, создай коллекцию с `size=1536, distance=Cosine`, залей только синтетические fixture-векторы с payload `tenant_id`, поставь payload-индекс на `tenant_id` и сравни латентность dense-поиска с фильтром. В отчёт — третья строка сравнения хранилищ. Self-hosted Qdrant по умолчанию без аутентификации: localhost-bind обязателен; для удалённого доступа сначала настрой `QDRANT__SERVICE__API_KEY`, TLS и сетевые ограничения по [документации Qdrant](https://qdrant.tech/documentation/security/).
2. **halfvec**: добавь колонку `embedding_half halfvec(1536)`, заполни `embedding::halfvec`, построй HNSW и сравни размер индексов через `pg_relation_size` и recall@5. Это готовый аргумент «в два раза меньше памяти без потери качества» — или опровержение на твоих данных.
3. **Контроль расхождения**: напиши SQL или скрипт, который сравнивает число чанков на документ между таблицей метаданных и векторным хранилищем и печатает расхождения. Это тот контроль, которого не хватило при миграции web-agent.

## Что проверить

- Сервис `docker compose ps pg` готов, расширение `vector` версии 0.8 или новее.
- `load.ipynb` загрузил все чанки дня 2, разделив на два tenant; размерность 1536.
- `explain.sql` показал Seq Scan до индекса и Index Scan после; записаны оба времени и эффект итеративного скана.
- `eval_pg.ipynb` выдал таблицу; Chroma и pgvector проверены на одинаковых tenant-снимках; расхождения Hit@5 разобраны, p50/p95 измерены после прогрева.
- `rls_demo.sql`: tenant видит только свои строки, без tenant — 0, попытка `WHERE tenant_id = 2` — 0.
- В `results.md` есть план миграции web-agent из пяти пунктов с оценкой часов и рисками.
- Коммит запушен в `iRoboTron/ai-labs`.
