# ~/proj/ai-labs/day6-serving-security/bench_ollama.py
"""Замеряет реальную скорость Ollama: сколько токенов в секунду и сколько ждать первый токен (TTFT)."""
import json
import statistics
import time

import httpx
import labkit

# --- НАСТРОЙКИ ---
MODELS = ["qwen2.5:7b-instruct-q4_K_M", "qwen2.5:7b-instruct-q8_0"]   # сравниваемые теги одной модели

OLLAMA = labkit.env("OLLAMA_URL", "http://127.0.0.1:11434")
PROMPT = "Объясни в пяти предложениях, что такое RAG, для DevOps-инженера."
LONG_PROMPT = PROMPT + "\nКонтекст:\n" + ("Ollama слушает порт 11434 и отдаёт API. " * 100)
CONTEXT = 4096


def run(model: str, prompt: str) -> dict:
    start, first, final, parts = time.perf_counter(), None, None, []
    with httpx.Client(timeout=600) as client:
        with client.stream("POST", f"{OLLAMA}/api/generate", json={"model": model, "prompt": prompt, "stream": True,
                           "options": {"num_ctx": CONTEXT, "num_predict": 200, "temperature": 0}}) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                event = json.loads(line)
                if event.get("error"):
                    raise RuntimeError("Ollama stream error")
                if event.get("response"):
                    if first is None:
                        first = time.perf_counter() - start
                    parts.append(event["response"])
                if event.get("done"):
                    final = event
    if final is None or first is None or final.get("eval_duration", 0) <= 0:
        raise RuntimeError("Неполный stream / нет токенов или timings")
    return {"tok_s": final["eval_count"] / (final["eval_duration"] / 1e9),
            "ttft_s": first, "prompt_tok": final.get("prompt_eval_count", 0),
            "prefill_s": final.get("prompt_eval_duration", 0) / 1e9,
            "load_s": final.get("load_duration", 0) / 1e9,
            "wall_s": time.perf_counter() - start, "answer": "".join(parts)}


def mem(model: str) -> str:
    response = httpx.get(f"{OLLAMA}/api/ps", timeout=10)
    response.raise_for_status()
    for entry in response.json().get("models", []):
        if entry["name"] == model:
            return f"{entry['size'] / 2**30:.1f} GiB, VRAM {entry.get('size_vram', 0) / 2**30:.1f} GiB"
    raise RuntimeError(f"Точная модель {model} отсутствует в /api/ps")


def unload(model: str):
    response = httpx.post(f"{OLLAMA}/api/generate", json={"model": model, "keep_alive": 0, "stream": False}, timeout=60)
    response.raise_for_status()


if __name__ == "__main__":
    print("| модель | память | tok/s median3 | TTFT median3, с | long tokens / prefill, с |")
    print("|---|---|---|---|---|")
    for model in MODELS:
        unload(model)
        try:
            run(model, "прогрев")  # не входит в статистику; кэш промпта не отключён
            short = [run(model, PROMPT) for _ in range(3)]
            long = run(model, LONG_PROMPT)
            print(f"| {model} | {mem(model)} | {statistics.median(r['tok_s'] for r in short):.1f} | "
                  f"{statistics.median(r['ttft_s'] for r in short):.3f} | {long['prompt_tok']} / {long['prefill_s']:.3f} |")
        finally:
            unload(model)  # не измерять Q8 при оставшейся в VRAM Q4
