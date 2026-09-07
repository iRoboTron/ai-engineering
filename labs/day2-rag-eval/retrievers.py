# ~/proj/ai-labs/day2-rag-eval/retrievers.py
"""Четыре способа искать релевантные чанки. Store — единая точка входа, используется во всех днях."""
import re
from functools import lru_cache

from common import load_config, load_rows, snapshot_path

WORD = re.compile(r"\w+", re.UNICODE)               # разбивает текст на слова для BM25

@lru_cache(maxsize=1)                                # модель стеммера грузится один раз на процесс
def stemmer():
    import snowballstemmer
    return snowballstemmer.stemmer("russian")        # приводит слова к основе: «нашёл»/«находит» → одна форма

def tokenize(text: str) -> list[str]:
    return stemmer().stemWords(WORD.findall(text.lower()))

@lru_cache(maxsize=1)                                # реранкер тяжёлый — загружаем один раз, не на каждый вопрос
def reranker():
    from sentence_transformers import CrossEncoder
    return CrossEncoder("BAAI/bge-reranker-v2-m3", max_length=512, device="cpu")

class Store:
    """Один снимок индекса плюс BM25 поверх него. tenant_id=None — видно всё; иначе — только свой tenant (день 3)."""

    def __init__(self, collection: str, embedder, tenant_id: int | None = None):
        import chromadb
        from rank_bm25 import BM25Okapi
        cfg = load_config(collection)
        if (cfg["embedder"], cfg["model"]) != (embedder.kind, embedder.model):
            raise ValueError("эмбеддер запроса не совпадает со снимком")
        self.col = chromadb.PersistentClient(path=str(snapshot_path(collection) / "chroma")).get_collection(collection)
        self.embedder, self.tenant_id = embedder, tenant_id
        rows = [r for r in load_rows(collection) if tenant_id is None or r["tenant_id"] == tenant_id]
        if not rows:
            raise ValueError("нет документов для выбранного tenant")
        self.by_id = {r["id"]: r for r in rows}
        self.ids = list(self.by_id)
        self.bm25 = BM25Okapi([tokenize(r["text"]) for r in rows])   # индекс BM25 строится в памяти при старте

    def dense(self, q: str, k: int) -> list[dict]:
        """Поиск по смыслу: вектор вопроса ближе всего к векторам нужных чанков."""
        args = {"query_embeddings": [self.embedder.embed_query(q)], "n_results": min(k, len(self.ids))}
        if self.tenant_id is not None:
            args["where"] = {"tenant_id": self.tenant_id}
        res = self.col.query(**args)
        return [self.by_id[i] for i in res["ids"][0]]

    def bm25_search(self, q: str, k: int) -> list[dict]:
        """Поиск по словам: хорош для точных терминов, кодов, названий."""
        scores = self.bm25.get_scores(tokenize(q))
        top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [self.by_id[self.ids[i]] for i in top if scores[i] > 0]

    def hybrid(self, q: str, k: int, candidates: int = 20, rrf_k: int = 60) -> list[dict]:
        """Складывает dense и BM25 через RRF (reciprocal rank fusion): чем выше место в обоих списках, тем выше итог."""
        fused = {}
        for ranked in (self.dense(q, candidates), self.bm25_search(q, candidates)):
            for pos, r in enumerate(ranked, start=1):
                fused[r["id"]] = fused.get(r["id"], 0.0) + 1.0 / (rrf_k + pos)
        return [self.by_id[i] for i in sorted(fused, key=fused.get, reverse=True)[:k]]

    def hybrid_rerank(self, q: str, k: int, candidates: int = 20) -> list[dict]:
        """Берёт кандидатов из hybrid, затем модель-реранкер читает пары (вопрос, чанк) вместе и уточняет порядок."""
        cands = self.hybrid(q, candidates, candidates=candidates)
        if not cands:
            return []
        scores = reranker().predict([(q, c["text"]) for c in cands])
        order = sorted(range(len(cands)), key=lambda i: float(scores[i]), reverse=True)[:k]
        return [cands[i] for i in order]
