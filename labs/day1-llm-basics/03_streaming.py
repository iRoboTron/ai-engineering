# ~/proj/ai-labs/day1-llm-basics/03_streaming.py
import time

from client import make_client, MODEL

client = make_client()
t0 = time.perf_counter()
first = None
usage = None

stream = client.chat.completions.create(
    model=MODEL,
    stream=True,
    stream_options={"include_usage": True},
    max_tokens=300,
    messages=[{"role": "user", "content": "Объясни в пяти предложениях, что такое RAG, для DevOps-инженера."}],
)
for event in stream:
    if event.usage:
        usage = event.usage  # приходит в последнем чанке
    if not event.choices:
        continue
    delta = event.choices[0].delta.content or ""
    if delta and first is None:
        first = time.perf_counter()
    print(delta, end="", flush=True)

t1 = time.perf_counter()
if first is None:
    raise RuntimeError("стрим не содержал текста: проверь отказ и finish_reason")
print(f"\n\nTTFT: {first - t0:.2f}s | всего: {t1 - t0:.2f}s", end="")
if usage and first:
    print(f" | out={usage.completion_tokens} → {max(0, usage.completion_tokens - 1) / max(t1 - first, 1e-9):.1f} tok/s")
else:
    print(" | usage в стриме не пришёл — провайдер не поддерживает include_usage")
