# ~/proj/ai-labs/day1-llm-basics/client.py
import labkit                 # читает .env: ключ, модель, прокси
from openai import OpenAI     # официальный клиент OpenAI; OpenRouter говорит на том же протоколе

# --- НАСТРОЙКИ (общие для всех скриптов дня 1) ---
BASE_URL = labkit.env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")   # адрес API
MODEL = labkit.env("LLM_MODEL", "anthropic/claude-haiku-4.5")                  # модель по умолчанию


def make_client(timeout: float = 60.0) -> OpenAI:
    """Создаёт клиент. Прокси из HTTPS_PROXY библиотека httpx подхватывает сама."""
    api_key = labkit.env("OPENROUTER_API_KEY", required=True)   # без ключа — понятная ошибка, а не тихий 401
    return OpenAI(
        base_url=BASE_URL,      # куда слать запросы
        api_key=api_key,        # заголовок Authorization
        timeout=timeout,        # секунд на один запрос
        max_retries=0,          # повторы делаем сами (шаг 7), чтобы их видеть
        default_headers={       # OpenRouter показывает эти поля в статистике приложений
            "HTTP-Referer": "https://ai-engineering.adelfos.ru",
            "X-Title": "ai-labs day1",
        },
    )
