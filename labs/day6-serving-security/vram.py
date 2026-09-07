# ~/proj/ai-labs/day6-serving-security/vram.py
import argparse

# слои, число KV-голов, размер головы — из config.json модели (num_hidden_layers, num_key_value_heads, hidden_size/num_attention_heads)
PRESETS = {
    "8b":  {"params_b": 8.0,  "layers": 32, "kv_heads": 8, "head_dim": 128},
    "14b": {"params_b": 14.7, "layers": 48, "kv_heads": 8, "head_dim": 128},
    "32b": {"params_b": 32.5, "layers": 64, "kv_heads": 8, "head_dim": 128},
    "70b": {"params_b": 70.6, "layers": 80, "kv_heads": 8, "head_dim": 128},
}
BYTES_PER_PARAM = {"fp16": 2.0, "int8": 1.0, "int4": 0.56}  # int4 с учётом масштабов квантизации


def estimate(preset: dict, bits: str, ctx: int, batch: int, kv_bytes: float = 2.0, overhead: float = 0.15) -> dict:
    weights = preset["params_b"] * 1e9 * BYTES_PER_PARAM[bits]
    kv_per_token = 2 * preset["layers"] * preset["kv_heads"] * preset["head_dim"] * kv_bytes  # K и V на каждый слой
    kv_total = kv_per_token * ctx * batch
    total = (weights + kv_total) * (1 + overhead)
    return {"weights_gb": weights / 2**30, "kv_per_token_kb": kv_per_token / 1024, "kv_total_gb": kv_total / 2**30, "total_gb": total / 2**30}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="8b", choices=PRESETS)
    ap.add_argument("--bits", default="int4", choices=BYTES_PER_PARAM)
    ap.add_argument("--ctx", type=int, default=8192)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--kv-fp8", action="store_true", help="квантованный KV-cache (1 байт)")
    a = ap.parse_args()
    e = estimate(PRESETS[a.model], a.bits, a.ctx, a.batch, kv_bytes=1.0 if a.kv_fp8 else 2.0)
    print(f"{a.model} {a.bits}, ctx={a.ctx}, batch={a.batch}")
    print(f"  веса:        {e['weights_gb']:6.1f} ГБ")
    print(f"  KV на токен: {e['kv_per_token_kb']:6.1f} КБ")
    print(f"  KV всего:    {e['kv_total_gb']:6.1f} ГБ")
    print(f"  итого (+15%):{e['total_gb']:6.1f} ГБ")
