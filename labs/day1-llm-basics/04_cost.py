# ~/proj/ai-labs/day1-llm-basics/04_cost.py
import httpx
import labkit

from client import BASE_URL, MODEL

# --- НАСТРОЙКИ ---
IN_TOKENS, OUT_TOKENS = 3500, 400           # типичный RAG-запрос: контекст + вопрос → короткий ответ
REQ_PER_MONTH = 1000 * 30                   # нагрузка сценария: тысяча запросов в день
CHEAP_MODEL = labkit.env("LLM_MODEL_CHEAP", "deepseek/deepseek-v4-flash-0731")  # модель для сравнения
MIN_CONTEXT = 100_000                       # фильтр для списка дешёвых моделей


def load_models() -> list[dict]:
    """Каталог моделей OpenRouter: цены, размер контекста, поддерживаемые параметры."""
    r = httpx.get(f"{BASE_URL}/models", timeout=30)  # прокси из HTTPS_PROXY подхватится сам
    r.raise_for_status()                    # исключение при HTTP-ошибке
    return r.json()["data"]


def price(models: list[dict], model_id: str) -> tuple[float, float, int | None]:
    """Цена за один токен входа и выхода (USD) и размер контекста."""
    for m in models:
        if m["id"] == model_id:
            p = m["pricing"]
            return float(p["prompt"]), float(p["completion"]), m.get("context_length")
    raise SystemExit(f"модель {model_id} не найдена в /models")


def monthly_cost(p_in: float, p_out: float) -> float:
    return (IN_TOKENS * p_in + OUT_TOKENS * p_out) * REQ_PER_MONTH


models = load_models()
cheap_candidates = sorted(                                                        # платные модели с большим контекстом
    (m for m in models if float(m["pricing"]["prompt"]) > 0 and (m.get("context_length") or 0) >= MIN_CONTEXT),
    key=lambda m: float(m["pricing"]["prompt"]),                                  # сортировка по цене входа
)[:10]
print(f"10 самых дешёвых моделей с контекстом ≥ {MIN_CONTEXT // 1000}k (цена за 1M входных токенов, USD):")
for m in cheap_candidates:
    print(f"  {float(m['pricing']['prompt']) * 1e6:8.3f}  {m['id']}")

for label, mid in (("основная", MODEL), ("дешёвая", CHEAP_MODEL)):
    p_in, p_out, ctx = price(models, mid)
    print(f"\n{label}: {mid} (контекст {ctx})")
    print(f"  вход ${p_in * 1e6:.2f}/1M, выход ${p_out * 1e6:.2f}/1M, отношение выход/вход: {p_out / p_in if p_in else None}")
    print(f"  один RAG-запрос: ${IN_TOKENS * p_in + OUT_TOKENS * p_out:.5f}")
    print(f"  {REQ_PER_MONTH} запросов в месяц: ${monthly_cost(p_in, p_out):.2f}")
