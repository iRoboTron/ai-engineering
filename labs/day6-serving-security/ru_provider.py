# ~/proj/ai-labs/day6-serving-security/ru_provider.py
"""Тот же клиент OpenAI, что и в дне 1, только base_url и заголовок другие — YandexGPT говорит на том же протоколе."""
import time

import labkit
from openai import OpenAI

FOLDER = labkit.env("YC_FOLDER_ID", required=True)      # идентификатор каталога Yandex Cloud
client = OpenAI(
    base_url="https://ai.api.cloud.yandex.net/v1",
    api_key=labkit.env("YC_API_KEY", required=True),
    default_headers={"OpenAI-Project": FOLDER},
    timeout=60,
    max_retries=0,
)
MODEL = labkit.env("YC_MODEL", f"gpt://{FOLDER}/yandexgpt/latest")

t0 = time.perf_counter()
r = client.chat.completions.create(
    model=MODEL, temperature=0, max_tokens=200,
    messages=[{"role": "system", "content": "Отвечай кратко, по-русски."},
              {"role": "user", "content": "Что такое RAG? Три предложения."}],
)
print(r.choices[0].message.content)
print(f"\nмодель: {MODEL} | TTFT+генерация: {time.perf_counter() - t0:.2f}s | usage: {r.usage}")
