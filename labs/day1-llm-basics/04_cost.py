# ~/proj/ai-labs/day1-llm-basics/04_cost.py
import os

import httpx

from client import BASE_URL, MODEL

IN_TOKENS, OUT_TOKENS, REQ_PER_MONTH = 3500, 400, 1000 * 30


def load_models() -> list[dict]:
    r = httpx.get(f"{BASE_URL}/models", timeout=30)  # прокси из HTTPS_PROXY подхватится сам
    r.raise_for_status()
    return r.json()["data"]


def price(models: list[dict], model_id: str) -> tuple[float, float, int | None]:
    for m in models:
        if m["id"] == model_id:
            p = m["pricing"]
            return float(p["prompt"]), float(p["completion"]), m.get("context_length")
    raise SystemExit(f"модель {model_id} не найдена в /models")


def monthly_cost(p_in: float, p_out: float) -> float:
    return (IN_TOKENS * p_in + OUT_TOKENS * p_out) * REQ_PER_MONTH


models = load_models()
cheap_candidates = sorted(
    (m for m in models if float(m["pricing"]["prompt"]) > 0 and (m.get("context_length") or 0) >= 100_000),
    key=lambda m: float(m["pricing"]["prompt"]),
)[:10]
print("10 самых дешёвых моделей с контекстом ≥ 100k (цена за 1M входных токенов, USD):")
for m in cheap_candidates:
    print(f"  {float(m['pricing']['prompt']) * 1e6:8.3f}  {m['id']}")

for label, mid in (("основная", MODEL), ("дешёвая", os.getenv("LLM_MODEL_CHEAP", ""))):
    if not mid:
        continue
    p_in, p_out, ctx = price(models, mid)
    print(f"\n{label}: {mid} (контекст {ctx})")
    print(f"  вход ${p_in * 1e6:.2f}/1M, выход ${p_out * 1e6:.2f}/1M, отношение выход/вход: {p_out / p_in if p_in else None}")
    print(f"  один RAG-запрос: ${IN_TOKENS * p_in + OUT_TOKENS * p_out:.5f}")
    print(f"  {REQ_PER_MONTH} запросов в месяц: ${monthly_cost(p_in, p_out):.2f}")
