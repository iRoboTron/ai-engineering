# ~/proj/ai-labs/day2-rag-eval/embed.py
"""Превращает текст в вектор. Один класс, два источника: платный API или бесплатная модель на CPU."""
import labkit
from functools import lru_cache

from openai import OpenAI


class Embedder:
    """kind='openrouter' — платный API, как в web-agent; kind='local' — sentence-transformers на CPU, бесплатно."""

    def __init__(self, kind: str, model: str):
        self.kind, self.model = kind, model
        if kind == "openrouter":
            self.client = OpenAI(
                base_url=labkit.env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                api_key=labkit.env("OPENROUTER_API_KEY", required=True),
                timeout=60,
                max_retries=2,
            )
        else:
            from sentence_transformers import SentenceTransformer   # тянет модель с Hugging Face при первом запуске

            self.st = SentenceTransformer(model, device="cpu")

    def _prefix(self, texts: list[str], role: str) -> list[str]:
        """Некоторые модели просят приписать 'query:'/'passage:' перед текстом — иначе поиск хуже. Легко забыть, поэтому здесь."""
        name = self.model.lower()
        if "e5" in name:
            p = "query: " if role == "query" else "passage: "
        elif "frida" in name:
            p = "search_query: " if role == "query" else "search_document: "
        else:
            p = ""  # bge-m3 и OpenAI префиксов не требуют
        return [p + t for t in texts]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Векторы для чанков документов — вызывается при индексации."""
        return self._embed(self._prefix(texts, "document"))

    def embed_query(self, text: str) -> list[float]:
        """Вектор одного поискового запроса; результат кэшируется — один вопрос эмбеддится только раз."""
        return list(self._query_cached(text))

    @lru_cache(maxsize=4096)                                  # повтор того же запроса не платит за эмбеддинг второй раз
    def _query_cached(self, text: str) -> tuple:
        return tuple(self._embed(self._prefix([text], "query"))[0])

    def _embed(self, texts: list[str]) -> list[list[float]]:
        if self.kind == "openrouter":
            out: list[list[float]] = []
            for s in range(0, len(texts), 64):                # пачками по 64, чтобы не упереться в лимит запроса
                r = self.client.embeddings.create(model=self.model, input=texts[s : s + 64])
                out.extend(d.embedding for d in sorted(r.data, key=lambda d: d.index))   # ответ может прийти не по порядку
            return out
        return self.st.encode(texts, normalize_embeddings=True, batch_size=16, show_progress_bar=False).tolist()
