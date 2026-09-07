# ~/proj/ai-labs/day1-llm-basics/05_retry.py
import random
import sys
import time

from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

from client import make_client, MODEL

RETRYABLE = (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)


def with_retries(fn, attempts: int = 5, base: float = 1.0, cap: float = 20.0):
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except RETRYABLE as exc:
            if attempt == attempts:
                raise
            delay = min(cap, base * 2 ** (attempt - 1)) + random.uniform(0, 0.5)  # экспонента + джиттер
            print(f"попытка {attempt} не удалась: {type(exc).__name__}; жду {delay:.1f}s", file=sys.stderr)
            time.sleep(delay)


client = make_client(timeout=float(sys.argv[1]) if len(sys.argv) > 1 else 60.0)
answer = with_retries(
    lambda: client.chat.completions.create(
        model=MODEL,
        max_tokens=60,
        messages=[{"role": "user", "content": "Одним предложением: зачем клиенту к LLM нужны ретраи?"}],
    )
)
print(answer.choices[0].message.content)
