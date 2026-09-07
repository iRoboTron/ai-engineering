# ~/proj/ai-labs/day3-pgvector/pgstore.py
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "day2-rag-eval"))
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
    def __init__(self, tenant_id: int, embedder: Embedder):
        if type(tenant_id) is not int or tenant_id <= 0:
            raise ValueError("tenant_id должен быть положительным int")
        import psycopg
        from pgvector.psycopg import register_vector
        self.conn = psycopg.connect(os.environ["PG_DSN"], autocommit=True)
        register_vector(self.conn)
        flags = self.conn.execute("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user").fetchone()
        if any(flags):
            self.conn.close()
            raise RuntimeError("PG_DSN приложения не может использовать SUPERUSER/BYPASSRLS")
        self.tenant_id, self.embedder = tenant_id, embedder

    def _rows(self, sql: str, params=None) -> list[dict]:
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
        return self._rows("SELECT id, tenant_id, filename, chunk_index, text FROM chunks ORDER BY id")

    def snapshot_config(self) -> dict:
        return self._rows("SELECT config FROM lab_snapshot")[0]["config"]

    def close(self) -> None:
        self.conn.close()
