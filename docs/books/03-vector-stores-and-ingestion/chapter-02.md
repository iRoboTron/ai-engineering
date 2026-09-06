# День 3. Лаба: pgvector рядом с Chroma

## Результат

Папка `~/proj/ai-labs/day3-pgvector/`: PostgreSQL с pgvector в Docker на homelab, те же чанки и векторы, что вчера в Chroma, HNSW и полнотекстовый индексы, гибридный поиск одним SQL-запросом, изоляция tenant через row-level security и таблица `results.md` — recall@k и латентность Chroma против pgvector на том же golden-наборе. Плюс план миграции web-agent с оценкой трудозатрат. Вчера ты доказал, что умеешь измерять поиск; сегодня — что умеешь выбирать и эксплуатировать хранилище.

## Карта лабы

```mermaid
flowchart LR
    CH["Chroma дня 2\nchunks_openai"] --> LD["load.py\nэкспорт векторов"]
    LD --> PG["PostgreSQL 17\npgvector, порт 5433"]
    SCH["schema.sql\nvector + tsvector\nHNSW + GIN + RLS"] --> PG
    PG --> D["dense\n<=> cosine"]
    PG --> F["fts\ntsvector russian"]
    D --> H["hybrid RRF\nодин SQL"]
    F --> H
    G["golden.jsonl\nдня 2"] --> EV["eval_pg.py"]
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

Нужны результаты дня 2: локальная Chroma с коллекцией `chunks_openai`, файлы `chunks.jsonl` и `golden.jsonl`. Postgres поднимаем отдельным контейнером на нестандартном порту, чтобы не задеть другие базы на машине.

```bash
cd ~/proj/ai-labs && source .venv/bin/activate && source .env
pip install -q "psycopg[binary]" pgvector numpy
mkdir -p day3-pgvector && cd day3-pgvector
```

## Шаг 1. PostgreSQL с pgvector в Docker (5 минут)

```yaml
# ~/proj/ai-labs/day3-pgvector/docker-compose.yml
services:
  pg:
    image: pgvector/pgvector:pg17
    container_name: ai-labs-pg
    environment:
      POSTGRES_USER: rag
      POSTGRES_PASSWORD: rag
      POSTGRES_DB: rag
    ports:
      - "127.0.0.1:5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

```bash
docker compose up -d
export PG_DSN="postgresql://rag:rag@127.0.0.1:5433/rag"
docker compose exec pg psql -U rag -d rag -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extversion FROM pg_extension WHERE extname='vector';"
```

Ожидаемо версия расширения `0.8.x` или новее. Запиши её — итеративный скан из шага 5 требует не ниже 0.8.0.

## Шаг 2. Схема: вектор, полнотекст, индексы, RLS

```sql
-- ~/proj/ai-labs/day3-pgvector/schema.sql
CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS chunks;
CREATE TABLE chunks (
    id          text PRIMARY KEY,
    tenant_id   int  NOT NULL,
    filename    text NOT NULL,
    chunk_index int  NOT NULL,
    text        text NOT NULL,
    embedding   vector(1536) NOT NULL,
    tsv         tsvector GENERATED ALWAYS AS (to_tsvector('russian', text)) STORED
);

-- индексы создадим ПОСЛЕ загрузки (шаг 4): так виден эффект и быстрее вставка
-- изоляция tenant: политика применяется даже к владельцу таблицы (FORCE)
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON chunks
    USING (tenant_id = current_setting('app.tenant_id', true)::int);
```

```bash
docker compose exec -T pg psql -U rag -d rag -v ON_ERROR_STOP=1 < schema.sql
```

Параметр `current_setting('app.tenant_id', true)` возвращает NULL, если tenant не задан, — тогда политика не пропускает ни одной строки. Это намеренно: код, забывший задать tenant, получает пусто, а не чужие данные.

## Шаг 3. Загрузка из Chroma

Векторы уже посчитаны вчера — платить за эмбеддинги второй раз не нужно. Половину документов отдадим tenant 1, половину tenant 2, чтобы было что изолировать.

```python
# ~/proj/ai-labs/day3-pgvector/load.py
import os
import sys

import chromadb
import numpy as np
import psycopg
from pgvector.psycopg import register_vector

DSN = os.environ["PG_DSN"]
CHROMA_PATH = os.path.expanduser("~/proj/ai-labs/day2-rag-eval/chroma")
COLLECTION = sys.argv[1] if len(sys.argv) > 1 else "chunks_openai"

col = chromadb.PersistentClient(path=CHROMA_PATH).get_collection(COLLECTION)
data = col.get(include=["embeddings", "documents", "metadatas"])
files = sorted({m["filename"] for m in data["metadatas"]})
tenant_of = {f: 1 if i < len(files) / 2 else 2 for i, f in enumerate(files)}  # две «компании»

rows = [
    (cid, tenant_of[m["filename"]], m["filename"], m["chunk_index"], doc, np.asarray(emb, dtype=np.float32))
    for cid, doc, m, emb in zip(data["ids"], data["documents"], data["metadatas"], data["embeddings"])
]

with psycopg.connect(DSN) as conn:
    register_vector(conn)
    with conn.cursor() as cur:
        cur.execute("SET app.tenant_id = '0'")  # владелец под FORCE RLS тоже фильтруется; для загрузки политика обходится ниже
        cur.execute("ALTER TABLE chunks DISABLE ROW LEVEL SECURITY")
        cur.executemany(
            "INSERT INTO chunks (id, tenant_id, filename, chunk_index, text, embedding) VALUES (%s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (id) DO UPDATE SET text = EXCLUDED.text, embedding = EXCLUDED.embedding",
            rows,
        )
        cur.execute("ALTER TABLE chunks ENABLE ROW LEVEL SECURITY")
        cur.execute("SELECT tenant_id, count(*), count(DISTINCT filename) FROM chunks GROUP BY tenant_id ORDER BY 1")
        for tenant, n_chunks, n_docs in cur.fetchall():
            print(f"tenant {tenant}: документов {n_docs}, чанков {n_chunks}")
    conn.commit()
print(f"размерность: {len(rows[0][5])}, всего строк: {len(rows)}")
```

Запуск: `python load.py`. Отключение RLS на время загрузки — осознанное действие администратора в одной транзакции; в проде загрузчик работает от роли с `BYPASSRLS` или под tenant. Вставка — upsert по детерминированному `id`, как в web-agent.

## Шаг 4. Индексы и EXPLAIN: увидеть разницу

Сначала запрос без индекса, потом с HNSW. На нескольких сотнях строк планировщик выберет последовательный скан даже при наличии индекса — это правильно с его стороны; для демонстрации индекс включаем принудительно.

```sql
-- ~/proj/ai-labs/day3-pgvector/explain.sql
-- один вектор запроса берём прямо из таблицы, чтобы не тащить его из Python
SET app.tenant_id = '1';
\set qvec 'SELECT embedding FROM chunks WHERE tenant_id = 1 ORDER BY id LIMIT 1'

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, filename, 1 - (embedding <=> (:qvec)) AS score
FROM chunks ORDER BY embedding <=> (:qvec) LIMIT 5;

CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS chunks_tsv_gin ON chunks USING gin (tsv);
ANALYZE chunks;

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

SET hnsw.iterative_scan = relaxed_order;
SELECT count(*) AS rows_with_iterative FROM (
  SELECT id FROM chunks WHERE filename = (SELECT filename FROM chunks WHERE tenant_id = 1 ORDER BY id DESC LIMIT 1)
  ORDER BY embedding <=> (:qvec) LIMIT 5) t;
RESET enable_seqscan;
```

```bash
docker compose exec -T pg psql -U rag -d rag -v ON_ERROR_STOP=1 < explain.sql
```

Что смотреть: в первом плане `Seq Scan` и `Sort`, во втором — `Index Scan using chunks_embedding_hnsw`; время выполнения обоих запиши. В двух последних запросах сравни число строк: без итеративного скана фильтр по одному файлу может дать меньше пяти строк, с ним — ровно пять. Если разницы нет — корпус мал и первые пять соседей и так из нужного файла; смени файл в подзапросе на редкий.

## Шаг 5. Три ретривера одним адаптером

```python
# ~/proj/ai-labs/day3-pgvector/pgstore.py
import os
import sys

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

sys.path.insert(0, os.path.expanduser("~/proj/ai-labs/day2-rag-eval"))
from embed import Embedder  # noqa: E402  — тот же эмбеддер запроса, что вчера

DENSE_SQL = """
SELECT id, filename, chunk_index, text, 1 - (embedding <=> %(v)s) AS score
FROM chunks ORDER BY embedding <=> %(v)s LIMIT %(k)s"""

FTS_SQL = """
SELECT id, filename, chunk_index, text, ts_rank_cd(tsv, q) AS score
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
SELECT c.id, c.filename, c.chunk_index, c.text,
       COALESCE(1.0 / (60 + dense.r), 0) + COALESCE(1.0 / (60 + fts.r), 0) AS score
FROM chunks c
LEFT JOIN dense ON dense.id = c.id
LEFT JOIN fts   ON fts.id   = c.id
WHERE dense.id IS NOT NULL OR fts.id IS NOT NULL
ORDER BY score DESC LIMIT %(k)s"""


class PgStore:
    def __init__(self, tenant_id: int, embedder: Embedder):
        self.conn = psycopg.connect(os.environ["PG_DSN"])
        register_vector(self.conn)
        self.conn.execute("SET app.tenant_id = %s", (str(tenant_id),))
        self.conn.execute("SET hnsw.ef_search = 40")
        self.embedder = embedder

    def _rows(self, sql: str, params: dict) -> list[dict]:
        cur = self.conn.execute(sql, params)
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def _vec(self, q: str) -> np.ndarray:
        return np.asarray(self.embedder.embed_query(q), dtype=np.float32)

    def dense(self, q: str, k: int) -> list[dict]:
        return self._rows(DENSE_SQL, {"v": self._vec(q), "k": k})

    def fts(self, q: str, k: int) -> list[dict]:
        return self._rows(FTS_SQL, {"q": q, "k": k})

    def hybrid(self, q: str, k: int, cand: int = 20) -> list[dict]:
        return self._rows(HYBRID_SQL, {"v": self._vec(q), "q": q, "k": k, "cand": cand})
```

Обрати внимание: в SQL нет `WHERE tenant_id` — фильтр добавляет политика RLS по `app.tenant_id`, заданному на соединении. Проверка: `python -c "from pgstore import PgStore; from embed import Embedder; s=PgStore(1, Embedder('openrouter','openai/text-embedding-3-small')); print([r['filename'] for r in s.hybrid('на каком порту слушает ollama', 3)])"` из папки `day3-pgvector` с `PG_DSN` в окружении.

## Шаг 6. Оценка и сравнение с Chroma

Переиспользуем `evaluate` из вчерашнего `eval.py` — метрики и формат таблицы должны совпадать, чтобы сравнение было честным. Golden-набор общий, но теперь документы разделены между двумя tenant: оцениваем каждый tenant по его вопросам.

```python
# ~/proj/ai-labs/day3-pgvector/eval_pg.py
import json
import os
import sys

sys.path.insert(0, os.path.expanduser("~/proj/ai-labs/day2-rag-eval"))
from embed import Embedder  # noqa: E402
from eval import evaluate   # noqa: E402

from pgstore import PgStore

golden = [json.loads(line) for line in open(os.path.expanduser("~/proj/ai-labs/day2-rag-eval/golden.jsonl"), encoding="utf-8") if line.strip()]
embedder = Embedder("openrouter", "openai/text-embedding-3-small")

print("| tenant | retriever | recall@1 | recall@3 | recall@5 | MRR | латентность, мс |")
print("|---|---|---|---|---|---|---|")
for tenant in (1, 2):
    store = PgStore(tenant, embedder)
    docs_of_tenant = {r[0] for r in store.conn.execute("SELECT DISTINCT filename FROM chunks").fetchall()}
    subset = [g for g in golden if g["doc"] in docs_of_tenant]
    if not subset:
        continue
    for name, fn in (("dense", store.dense), ("fts", store.fts), ("hybrid RRF", store.hybrid)):
        r = evaluate(name, fn, subset)
        print(f"| {tenant} ({len(subset)} q) | {r['retriever']} | {r['recall@1']:.2f} | {r['recall@3']:.2f} | {r['recall@5']:.2f} | {r['mrr']:.2f} | {r['latency_ms']:.0f} |")
```

Запуск: `python eval_pg.py`. Dense в pgvector должен давать те же попадания, что dense в Chroma (те же векторы, косинус) — если нет, ищи разницу в метрике расстояния или в `ef_search`. Полнотекстовый поиск Postgres против вчерашнего BM25 со стеммингом — разные алгоритмы, разница ожидаема в обе стороны; запиши, какая.

## Шаг 7. RLS: доказать, что утечки нет

```sql
-- ~/proj/ai-labs/day3-pgvector/rls_demo.sql
SET app.tenant_id = '1';
SELECT tenant_id, count(*) FROM chunks GROUP BY tenant_id;          -- только tenant 1
SET app.tenant_id = '2';
SELECT tenant_id, count(*) FROM chunks GROUP BY tenant_id;          -- только tenant 2
RESET app.tenant_id;
SELECT count(*) AS visible_without_tenant FROM chunks;               -- 0: забытый tenant = пусто, не утечка
-- попытка обойти фильтром в запросе:
SET app.tenant_id = '1';
SELECT count(*) AS leak_attempt FROM chunks WHERE tenant_id = 2;     -- 0
```

```bash
docker compose exec -T pg psql -U rag -d rag -v ON_ERROR_STOP=1 < rls_demo.sql
```

Четыре результата — в отчёт. Это ответ на вопрос «как гарантируете изоляцию», который можно показать, а не рассказать.

## Шаг 8. Парсинг с таблицами: Docling против pypdf (30 минут, по желанию)

Если в корпусе есть PDF с таблицей — сравни, что извлекают `pypdf` (как в web-agent) и Docling. Установка Docling тяжёлая (модели раскладки, сотни мегабайт), делай только при запасе времени.

```bash
pip install -q docling
python -c "from docling.document_converter import DocumentConverter; import sys; print(DocumentConverter().convert(sys.argv[1]).document.export_to_markdown()[:3000])" corpus-sample.pdf
python -c "from pypdf import PdfReader; import sys; print((PdfReader(sys.argv[1]).pages[0].extract_text() or '')[:3000])" corpus-sample.pdf
```

Смотри на таблицу: у pypdf строки и колонки склеятся в поток слов, у Docling — Markdown-таблица. В отчёт: пример из трёх строк обоих вариантов и вывод, для каких документов web-agent стоило бы включить Docling как опцию, а для каких лёгкий парсер достаточен.

## Шаг 9. results.md: сравнение и план миграции

```markdown
# День 3 — pgvector рядом с Chroma (дата, pgvector x.y.z, чанков N)

## Качество и латентность (тот же golden-набор)
| хранилище | retriever | recall@5 | MRR | латентность, мс |
| Chroma (день 2) | dense | … | … | … |
| pgvector | dense | … | … | … |
| pgvector | fts (ts_rank_cd) | … | … | … |
| pgvector | hybrid RRF в SQL | … | … | … |

## EXPLAIN
- без индекса: Seq Scan, … мс; с HNSW: Index Scan, … мс
- фильтр + LIMIT 5: без iterative_scan … строк, с relaxed_order … строк

## RLS
- tenant 1 видит …, tenant 2 видит …, без tenant 0, попытка WHERE tenant_id=2 → 0

## План миграции web-agent Chroma → pgvector
1. Таблица chunks в существующем Postgres web-agent (tenant_id = site_id), RLS, HNSW, GIN. Alembic-миграция.
2. Двойная запись в doc-parser: reindex пишет в Chroma и в Postgres (флаг). Backfill существующих коллекций скриптом.
3. retriever.py: режим dense | hybrid по настройке сайта; SET app.tenant_id на соединении из пула.
4. Сравнение на golden-наборе tenant ksm; переключение чтения на pgvector; неделя наблюдения; удаление Chroma из compose.
5. Оценка: … часов; риски: долгая сборка HNSW на большом tenant (строить CONCURRENTLY), размер БД (+ N ГБ), пул соединений и SET на сессии (PgBouncer в transaction mode требует SET LOCAL в транзакции).

## Выводы
```

Коммит: `git add -A && git commit -m "day3: pgvector — schema, HNSW, hybrid SQL, RLS, eval vs Chroma"`, push.

## Если не получилось

- **`psycopg` не видит `vector`** — забыт `register_vector(conn)` после подключения; без него numpy-массив не сериализуется.
- **`current_setting` падает `unrecognized configuration parameter`** — используй двухсоставное имя `app.tenant_id` (с точкой) и `current_setting('app.tenant_id', true)`.
- **Все запросы возвращают 0 строк** — RLS работает, а `app.tenant_id` не задан на этом соединении; `SET` действует на сессию, а не на базу.
- **Индекс не используется в EXPLAIN** — таблица мала; `SET enable_seqscan = off` только для демонстрации; на проде планировщик переключится сам с ростом.
- **`iterative_scan` — unrecognized** — pgvector ниже 0.8; обнови образ `pgvector/pgvector:pg17`.
- **Полнотекст не находит очевидное** — конфигурация `russian` должна стоять и в `to_tsvector`, и в `plainto_tsquery`; проверь `SELECT to_tsvector('russian', 'абонементы')`.
- **Docling ставится вечно** — это нормально, отложи в stretch; лаба засчитывается без шага 8.

## Практика

1. **Qdrant за 20 минут**: `docker run -d -p 6333:6333 qdrant/qdrant`, `pip install qdrant-client`, создай коллекцию с `size=1536, distance=Cosine`, залей те же векторы с payload `tenant_id`, поставь payload-индекс на `tenant_id` и сравни латентность dense-поиска с фильтром. В отчёт — третья строка сравнения хранилищ.
2. **halfvec**: добавь колонку `embedding_half halfvec(1536)`, заполни `embedding::halfvec`, построй HNSW и сравни размер индексов через `pg_relation_size` и recall@5. Это готовый аргумент «в два раза меньше памяти без потери качества» — или опровержение на твоих данных.
3. **Контроль расхождения**: напиши SQL или скрипт, который сравнивает число чанков на документ между таблицей метаданных и векторным хранилищем и печатает расхождения. Это тот контроль, которого не хватило при миграции web-agent.

## Что проверить

- Контейнер `ai-labs-pg` работает, расширение `vector` версии 0.8 или новее.
- `load.py` загрузил все чанки дня 2, разделив на два tenant; размерность 1536.
- `explain.sql` показал Seq Scan до индекса и Index Scan после; записаны оба времени и эффект итеративного скана.
- `eval_pg.py` выдал таблицу; dense pgvector совпадает с dense Chroma по recall@5 в пределах одного попадания, иначе причина найдена.
- `rls_demo.sql`: tenant видит только свои строки, без tenant — 0, попытка `WHERE tenant_id = 2` — 0.
- В `results.md` есть план миграции web-agent из пяти пунктов с оценкой часов и рисками.
- Коммит запушен в `iRoboTron/ai-labs`.
