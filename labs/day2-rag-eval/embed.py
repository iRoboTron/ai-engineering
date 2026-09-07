# ~/proj/ai-labs/day2-rag-eval/embed.py
import os
from functools import lru_cache

from openai import OpenAI


class Embedder:
    """kind='openrouter' — как в web-agent; kind='local' — sentence-transformers на CPU."""

    def __init__(self, kind: str, model: str):
        self.kind, self.model = kind, model
        if kind == "openrouter":
            self.client = OpenAI(
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                api_key=os.environ["OPENROUTER_API_KEY"],
                timeout=60,
                max_retries=2,
            )
        else:
            from sentence_transformers import SentenceTransformer

            self.st = SentenceTransformer(model, device="cpu")

    def _prefix(self, texts: list[str], role: str) -> list[str]:
        name = self.model.lower()
        if "e5" in name:
            p = "query: " if role == "query" else "passage: "
        elif "frida" in name:
            p = "search_query: " if role == "query" else "search_document: "
        else:
            p = ""  # bge-m3 и OpenAI префиксов не требуют
        return [p + t for t in texts]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(self._prefix(texts, "document"))

    def embed_query(self, text: str) -> list[float]:
        return list(self._query_cached(text))

    @lru_cache(maxsize=4096)
    def _query_cached(self, text: str) -> tuple:
        return tuple(self._embed(self._prefix([text], "query"))[0])

    def _embed(self, texts: list[str]) -> list[list[float]]:
        if self.kind == "openrouter":
            out: list[list[float]] = []
            for s in range(0, len(texts), 64):
                r = self.client.embeddings.create(model=self.model, input=texts[s : s + 64])
                out.extend(d.embedding for d in sorted(r.data, key=lambda d: d.index))
            return out
        return self.st.encode(texts, normalize_embeddings=True, batch_size=16, show_progress_bar=False).tolist()
