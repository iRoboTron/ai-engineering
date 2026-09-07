# ~/proj/ai-labs/day3-pgvector/eval_pg.py
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "day2-rag-eval"))
from common import golden_for_rows, load_config, load_golden, load_rows
from eval import evaluate

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", nargs="?", default="chunks_openai")
    ap.add_argument("--golden")
    a = ap.parse_args()
    cfg, rows = load_config(a.collection), load_rows(a.collection)
    golden = golden_for_rows(load_golden(a.golden), rows, require_all=True)
    from embed import Embedder
    from retrievers import Store
    from pgstore import PgStore
    embedder = Embedder(cfg["embedder"], cfg["model"])
    t0 = time.perf_counter()
    for g in golden:
        embedder.embed_query(g["q"])
    print(f"query embeddings, вне поиска: {time.perf_counter() - t0:.2f} s")
    print("| tenant | retriever | Hit@5 | MRR@5 | p50 ms | p95 ms |")
    print("|---|---|---|---|---|---|")
    for tenant in sorted({r["tenant_id"] for r in rows}):
        subset_rows = [r for r in rows if r["tenant_id"] == tenant]
        subset = golden_for_rows(golden, subset_rows)
        if not subset:
            continue
        chroma = Store(a.collection, embedder, tenant_id=tenant)
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

if __name__ == "__main__":
    main()
