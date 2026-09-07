# ~/proj/ai-labs/day3-pgvector/load.py
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "day2-rag-eval"))
from common import load_config, snapshot_path

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", nargs="?", default="chunks_openai")
    ap.add_argument("--replace-lab-data", action="store_true")
    a = ap.parse_args()
    config = load_config(a.collection)
    if config["dimension"] != 1536:
        raise SystemExit("эта учебная схема vector(1536); для другой модели нужна отдельная схема")
    import chromadb
    import numpy as np
    import psycopg
    from pgvector.psycopg import register_vector
    from psycopg.types.json import Jsonb
    col = chromadb.PersistentClient(path=str(snapshot_path(a.collection) / "chroma")).get_collection(a.collection)
    data = col.get(include=["embeddings", "documents", "metadatas"])
    rows = [(cid, m["tenant_id"], m["filename"], m["chunk_index"], doc, np.asarray(emb, dtype=np.float32))
            for cid, doc, m, emb in zip(data["ids"], data["documents"], data["metadatas"], data["embeddings"])]
    if not rows:
        raise SystemExit("снимок пуст")
    with psycopg.connect(os.environ["PG_ADMIN_DSN"]) as conn:
        register_vector(conn)
        if conn.execute("SELECT current_database(), current_user").fetchone() != ("rag", "rag_admin"):
            raise RuntimeError("загрузчик разрешён только в учебной БД rag от rag_admin")
        if conn.execute("SELECT count(*) FROM chunks").fetchone()[0] and not a.replace_lab_data:
            raise RuntimeError("таблица непуста; проверь DSN и явно разреши --replace-lab-data")
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
