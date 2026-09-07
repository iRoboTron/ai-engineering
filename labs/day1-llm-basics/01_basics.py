# ~/proj/ai-labs/day1-llm-basics/01_basics.py
from client import make_client, MODEL

client = make_client()


def ask(prompt: str, temperature: float):
    r = client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        max_tokens=120,
        messages=[
            {"role": "system", "content": "Отвечай одним коротким предложением, без пояснений."},
            {"role": "user", "content": prompt},
        ],
    )
    if not r.choices or not r.choices[0].message.content or r.usage is None:
        raise RuntimeError("нет текста/usage: проверь отказ, лимит ответа и возможности провайдера")
    return r.choices[0].message.content.strip(), r.usage


QUESTION = "Придумай название для сервиса, который отвечает на вопросы по документам компании."
for t in (0.0, 1.0):
    print(f"\n=== temperature={t} ===")
    for i in range(3):
        text, usage = ask(QUESTION, t)
        print(f"{i + 1}. {text}   [in={usage.prompt_tokens} out={usage.completion_tokens}]")

print("\n=== токены: русский против английского ===")
for s in (
    "The quick brown fox jumps over the lazy dog near the river.",
    "Быстрая рыжая лиса перепрыгивает через ленивую собаку у реки.",
):
    r = client.chat.completions.create(model=MODEL, max_tokens=1, messages=[{"role": "user", "content": s}])
    print(f"{r.usage.prompt_tokens:4d} токенов | {len(s):3d} символов | {s}")
