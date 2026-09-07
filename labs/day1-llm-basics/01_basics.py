# ~/proj/ai-labs/day1-llm-basics/01_basics.py
import labkit  # noqa: F401  читает .env
from client import make_client, MODEL

# --- НАСТРОЙКИ ---
QUESTION = "Придумай название для сервиса, который отвечает на вопросы по документам компании."
TEMPERATURES = (0.0, 1.0)     # 0 — почти детерминированно, 1 — разнообразно
REPEATS = 3                   # сколько раз задать один вопрос при каждой температуре
SAMPLES = (                   # пара фраз одинакового смысла для сравнения токенов
    "The quick brown fox jumps over the lazy dog near the river.",
    "Быстрая рыжая лиса перепрыгивает через ленивую собаку у реки.",
)

client = make_client()


def ask(prompt: str, temperature: float):
    """Один запрос к модели. Возвращает текст ответа и usage — счётчики токенов."""
    r = client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        max_tokens=120,                                   # потолок длины ответа
        messages=[
            {"role": "system", "content": "Отвечай одним коротким предложением, без пояснений."},  # правила
            {"role": "user", "content": prompt},                                                    # вопрос
        ],
    )
    if not r.choices or not r.choices[0].message.content or r.usage is None:
        raise RuntimeError("нет текста/usage: проверь отказ, лимит ответа и возможности провайдера")
    return r.choices[0].message.content.strip(), r.usage


print(f"модель: {MODEL}")
for t in TEMPERATURES:
    print(f"\n=== temperature={t} ===")
    for i in range(REPEATS):
        text, usage = ask(QUESTION, t)
        print(f"{i + 1}. {text}   [in={usage.prompt_tokens} out={usage.completion_tokens}]")   # in — токены запроса, out — ответа

print("\n=== токены: русский против английского ===")
for s in SAMPLES:
    r = client.chat.completions.create(model=MODEL, max_tokens=1, messages=[{"role": "user", "content": s}])  # ответ не нужен, нужен подсчёт входа
    print(f"{r.usage.prompt_tokens:4d} токенов | {len(s):3d} символов | {s}")
