# ~/proj/ai-labs/day6-serving-security/ru_provider.py
import os
import time

from openai import OpenAI

FOLDER = os.environ["YC_FOLDER_ID"]
client = OpenAI(
    base_url="https://ai.api.cloud.yandex.net/v1",
    api_key=os.environ["YC_API_KEY"],
    default_headers={"OpenAI-Project": FOLDER},
    timeout=60,
    max_retries=0,
)
MODEL = os.getenv("YC_MODEL", f"gpt://{FOLDER}/yandexgpt/latest")

t0 = time.perf_counter()
r = client.chat.completions.create(
    model=MODEL, temperature=0, max_tokens=200,
    messages=[{"role": "system", "content": "Отвечай кратко, по-русски."},
              {"role": "user", "content": "Что такое RAG? Три предложения."}],
)
print(r.choices[0].message.content)
print(f"\nмодель: {MODEL} | TTFT+генерация: {time.perf_counter() - t0:.2f}s | usage: {r.usage}")
