# ~/proj/ai-labs/day1-llm-basics/client.py
import os
from openai import OpenAI

BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4.6")


def make_client(timeout: float = 60.0) -> OpenAI:
    """Клиент OpenAI-совместимого API. Прокси берётся из HTTPS_PROXY автоматически (httpx)."""
    api_key = os.environ["OPENROUTER_API_KEY"]  # KeyError лучше, чем тихий 401
    return OpenAI(
        base_url=BASE_URL,
        api_key=api_key,
        timeout=timeout,
        max_retries=0,
        default_headers={
            "HTTP-Referer": "https://ai-engineering.adelfos.ru",
            "X-Title": "ai-labs day1",
        },
    )
