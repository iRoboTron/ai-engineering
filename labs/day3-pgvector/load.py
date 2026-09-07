# ~/proj/ai-labs/day3-pgvector/load.py
"""Копирует вчерашний снимок Chroma в Postgres: те же id, тексты и векторы, без пересчёта эмбеддингов."""
import labkit
labkit.use_day("day2-rag-eval")  # добавляет day2-rag-eval в sys.path — оттуда common.py
from common import load_config, snapshot_path

# --- НАСТРОЙКИ ---
COLLECTION = "chunks_openai"   # снимок из day2-rag-eval/index.py, который загружаем
REPLACE_LAB_DATA = False       # True — разрешить перезаписать уже загруженную учебную таблицу (не для прода!)


def main() -> None:
    config = load_config(COLLECTION)
    if config["dimension"] != 1536:
        raise SystemExit("эта учебная схема vector(1536); для другой модели нужна отдельная схема")
    import chromadb
    import numpy as np
    import psycopg
    from pgvector.psycopg import register_vector
    from psycopg.types.json import Jsonb
    col = chromadb.PersistentClient(path=str(snapshot_path(COLLECTION) / "chroma")).get_collection(COLLECTION)
    data = col.get(include=["embeddings", "documents", "metadatas"])
    rows = [(cid, m["tenant_id"], m["filename"], m["chunk_index"], doc, np.asarray(emb, dtype=np.float32))
            for cid, doc, m, emb in zip(data["ids"], data["documents"], data["metadatas"], data["embeddings"])]
    if not rows:
        raise SystemExit("снимок пуст")
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

if __name__ == "__main__":
    main()
