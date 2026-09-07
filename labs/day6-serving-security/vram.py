# ~/proj/ai-labs/day6-serving-security/vram.py
"""Считает, сколько видеопамяти займёт модель: веса плюс KV-cache для заданного контекста и параллельных запросов.
Внизу — список сценариев для сравнения; один запуск печатает таблицу по всем сразу, редактировать SCENARIOS,
чтобы добавить свою комбинацию."""

# слои, число KV-голов, размер головы — из config.json модели (num_hidden_layers, num_key_value_heads, hidden_size/num_attention_heads)
PRESETS = {
    "8b":  {"params_b": 8.0,  "layers": 32, "kv_heads": 8, "head_dim": 128},
    "14b": {"params_b": 14.7, "layers": 48, "kv_heads": 8, "head_dim": 128},
    "32b": {"params_b": 32.5, "layers": 64, "kv_heads": 8, "head_dim": 128},
    "70b": {"params_b": 70.6, "layers": 80, "kv_heads": 8, "head_dim": 128},
}
BYTES_PER_PARAM = {"fp16": 2.0, "int8": 1.0, "int4": 0.56}  # int4 с учётом масштабов квантизации

# --- НАСТРОЙКИ: список сценариев (модель, битность, контекст, параллельные запросы, fp8 для KV-cache) ---
SCENARIOS = [
    {"model": "8b", "bits": "fp16", "ctx": 8192, "batch": 1, "kv_fp8": False},
    {"model": "8b", "bits": "int4", "ctx": 8192, "batch": 4, "kv_fp8": False},
    {"model": "14b", "bits": "int4", "ctx": 8192, "batch": 4, "kv_fp8": False},
    {"model": "70b", "bits": "int4", "ctx": 8192, "batch": 32, "kv_fp8": False},
    {"model": "70b", "bits": "int4", "ctx": 8192, "batch": 32, "kv_fp8": True},
]


def estimate(preset: dict, bits: str, ctx: int, batch: int, kv_bytes: float = 2.0, overhead: float = 0.15) -> dict:
    weights = preset["params_b"] * 1e9 * BYTES_PER_PARAM[bits]
    kv_per_token = 2 * preset["layers"] * preset["kv_heads"] * preset["head_dim"] * kv_bytes  # K и V на каждый слой
    kv_total = kv_per_token * ctx * batch
    total = (weights + kv_total) * (1 + overhead)
    return {"weights_gb": weights / 2**30, "kv_per_token_kb": kv_per_token / 1024, "kv_total_gb": kv_total / 2**30, "total_gb": total / 2**30}


if __name__ == "__main__":
    for s in SCENARIOS:
        e = estimate(PRESETS[s["model"]], s["bits"], s["ctx"], s["batch"], kv_bytes=1.0 if s["kv_fp8"] else 2.0)
        print(f"{s['model']} {s['bits']}, ctx={s['ctx']}, batch={s['batch']}{' kv-fp8' if s['kv_fp8'] else ''}")
        print(f"  веса:        {e['weights_gb']:6.1f} ГБ")
        print(f"  KV на токен: {e['kv_per_token_kb']:6.1f} КБ")
        print(f"  KV всего:    {e['kv_total_gb']:6.1f} ГБ")
        print(f"  итого (+15%):{e['total_gb']:6.1f} ГБ\n")
