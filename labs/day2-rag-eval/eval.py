# ~/proj/ai-labs/day2-rag-eval/eval.py
import argparse
import math
import time
from statistics import mean, median

from common import golden_for_rows, load_config, load_golden, load_rows

KS = (1, 3, 5)

def is_hit(result: dict, gold: dict) -> bool:
    return result["filename"] == gold["doc"] and gold["must"].lower() in result["text"].lower()

def evaluate(name: str, search, golden: list[dict], k_max: int = 5, repeats: int = 3) -> dict:
    if not golden or repeats < 1 or k_max < max(KS):
        raise ValueError("нужны вопросы, repeats >= 1 и k_max >= 5")
    warm_t0 = time.perf_counter()
    for g in golden:
        search(g["q"], k_max)  # модель, соединения и query-cache вне steady-state таймера
    warmup_ms = 1000 * (time.perf_counter() - warm_t0)
    ranks, latencies = [], []
    for repeat in range(repeats):
        for g in golden:
            t0 = time.perf_counter()
            results = search(g["q"], k_max)
            latencies.append(1000 * (time.perf_counter() - t0))
            if repeat == 0:
                ranks.append(next((pos + 1 for pos, r in enumerate(results) if is_hit(r, g)), None))
    row = {"retriever": name, "latency_ms": median(latencies),
           "p95_ms": sorted(latencies)[math.ceil(.95 * len(latencies)) - 1],
           "warmup_ms": warmup_ms, "samples": len(latencies)}
    # Ключи recall@k оставлены для совместимости адаптеров; здесь это Hit@k, не общий recall.
    for k in KS:
        row[f"recall@{k}"] = sum(r is not None and r <= k for r in ranks) / len(ranks)
    row["mrr"] = mean(1.0 / r if r else 0.0 for r in ranks)  # MRR@k_max
    row["misses"] = [g["q"] for g, r in zip(golden, ranks) if r is None]
    return row

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("collection", nargs="?", default="chunks_openai")
    ap.add_argument("--golden")
    ap.add_argument("--repeats", type=int, default=3)
    a = ap.parse_args()
    cfg = load_config(a.collection)
    golden = golden_for_rows(load_golden(a.golden), load_rows(a.collection), require_all=True)
    from embed import Embedder
    from retrievers import Store
    embedder = Embedder(cfg["embedder"], cfg["model"])
    t0 = time.perf_counter()
    for g in golden:
        embedder.embed_query(g["q"])
    print(f"query embeddings (один раз, вне поиска): {time.perf_counter() - t0:.2f} s")
    store = Store(a.collection, embedder)
    print(f"snapshot={cfg['dataset_hash']} questions={len(golden)} repeats={a.repeats}")
    print("| retriever | Hit@1 | Hit@3 | Hit@5 | MRR@5 | p50 ms | p95 ms | warmup ms |")
    print("|---|---|---|---|---|---|---|---|")
    for name, fn in (("dense", store.dense), ("bm25", store.bm25_search), ("hybrid RRF", store.hybrid), ("hybrid + rerank", store.hybrid_rerank)):
        r = evaluate(name, fn, golden, repeats=a.repeats)
        print(f"| {name} | {r['recall@1']:.2f} | {r['recall@3']:.2f} | {r['recall@5']:.2f} | {r['mrr']:.2f} | {r['latency_ms']:.1f} | {r['p95_ms']:.1f} | {r['warmup_ms']:.0f} |")
        if r["misses"]:
            print("Промахи:", " | ".join(r["misses"][:6]))

if __name__ == "__main__":
    main()
