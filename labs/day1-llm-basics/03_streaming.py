# ~/proj/ai-labs/day1-llm-basics/03_streaming.py
import time

import labkit  # noqa: F401  читает .env
from client import make_client, MODEL

# --- НАСТРОЙКИ ---
PROMPT = "Объясни в пяти предложениях, что такое RAG, для DevOps-инженера."
MAX_TOKENS = 300

client = make_client()
t0 = time.perf_counter()      # момент отправки запроса
first = None                  # момент первого токена (для TTFT)
usage = None                  # счётчики токенов, приходят в последнем чанке

stream = client.chat.completions.create(
    model=MODEL,
    stream=True,                                  # ответ приходит кусками, а не целиком
    stream_options={"include_usage": True},       # попросить usage в конце стрима
    max_tokens=MAX_TOKENS,
    messages=[{"role": "user", "content": PROMPT}],
)
for event in stream:                              # каждый event — один кусок ответа
    if event.usage:
        usage = event.usage                       # последний чанк: только usage, без текста
    if not event.choices:
        continue
    delta = event.choices[0].delta.content or ""  # новые символы в этом куске
    if delta and first is None:
        first = time.perf_counter()               # первый токен пришёл
    print(delta, end="", flush=True)              # печатаем сразу, как чат в браузере

t1 = time.perf_counter()
if first is None:
    raise RuntimeError("стрим не содержал текста: проверь отказ и finish_reason")
print(f"\n\nTTFT: {first - t0:.2f}s | всего: {t1 - t0:.2f}s", end="")     # TTFT — время до первого токена
if usage and first:
    print(f" | out={usage.completion_tokens} → {max(0, usage.completion_tokens - 1) / max(t1 - first, 1e-9):.1f} tok/s")  # скорость генерации
else:
    print(" | usage в стриме не пришёл — провайдер не поддерживает include_usage")
