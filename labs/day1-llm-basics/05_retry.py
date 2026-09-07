# ~/proj/ai-labs/day1-llm-basics/05_retry.py
import random
import sys
import time

import labkit  # noqa: F401  читает .env
from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError   # ошибки, после которых есть смысл повторить

from client import make_client, MODEL

# --- НАСТРОЙКИ ---
TIMEOUT = 60.0      # секунд на запрос; поставь 0.3, чтобы увидеть ретраи по таймауту
ATTEMPTS = 5        # максимум попыток
BASE_DELAY = 1.0    # первая пауза, дальше удвоение: 1, 2, 4, 8…
MAX_DELAY = 20.0    # потолок паузы
PROMPT = "Одним предложением: зачем клиенту к LLM нужны ретраи?"

RETRYABLE = (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)   # 429, сеть, таймаут, 5xx


def with_retries(fn, attempts: int = ATTEMPTS, base: float = BASE_DELAY, cap: float = MAX_DELAY):
    """Вызывает fn(); при временной ошибке ждёт и повторяет. Exponential backoff с джиттером."""
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except RETRYABLE as exc:
            if attempt == attempts:
                raise                                                             # попытки кончились — ошибка наверх
            delay = min(cap, base * 2 ** (attempt - 1)) + random.uniform(0, 0.5)  # экспонента + случайный сдвиг
            print(f"попытка {attempt} не удалась: {type(exc).__name__}; жду {delay:.1f}s", file=sys.stderr)
            time.sleep(delay)


client = make_client(timeout=TIMEOUT)
answer = with_retries(
    lambda: client.chat.completions.create(          # lambda: сам запрос упакован в функцию без аргументов
        model=MODEL,
        max_tokens=60,
        messages=[{"role": "user", "content": PROMPT}],
    )
)
print(answer.choices[0].message.content)
