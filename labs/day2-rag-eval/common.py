# ~/proj/ai-labs/day2-rag-eval/common.py
"""Общие функции: где лежит снимок индекса, как читать golden-вопросы, как считать Hit@k/MRR.
Импортируется другими файлами дня и днём 3 (eval_pg.py), поэтому остаётся обычным модулем, не ноутбуком."""
import hashlib
import json
import math
import re
import time
from pathlib import Path
from statistics import mean, median

KS = (1, 3, 5)

ROOT = Path(__file__).resolve().parent          # папка day2-rag-eval, не зависит от того, откуда запущен скрипт
FIXTURES = ROOT.parent / "fixtures"              # публичные учебные документы курса

def snapshot_path(collection: str) -> Path:
    """Папка одного снимка индекса: .local/<имя коллекции>/."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{2,63}", collection):
        raise ValueError("collection: 3–64 буквы, цифры, дефис или подчёркивание")
    return ROOT / ".local" / collection

def load_config(collection: str) -> dict:
    """Настройки, с которыми был построен снимок: модель эмбеддингов, размер чанка и т.д."""
    return json.loads((snapshot_path(collection) / "config.json").read_text(encoding="utf-8"))

def load_rows(collection: str) -> list[dict]:
    """Все чанки снимка построчным JSON — по ним строится BM25 и разбираются промахи."""
    return [json.loads(line) for line in (snapshot_path(collection) / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

def load_golden(path=None) -> list[dict]:
    """Проверочные вопросы: q — вопрос, doc — где должен быть ответ, must — обязательная фраза."""
    source = Path(path) if path else FIXTURES / "golden.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows or any(not all(isinstance(r.get(k), str) and r[k].strip() for k in ("q", "doc", "must")) for r in rows):
        raise ValueError("golden: требуется непустой список q/doc/must")
    return rows

def tenant_map(filenames) -> dict[str, int]:
    """Делит документы поровну между двумя учебными арендаторами (пригодится в дне 3)."""
    names = sorted(set(filenames))
    if len(names) < 2:
        raise ValueError("для сравнения tenant нужны минимум два документа")
    boundary = (len(names) + 1) // 2
    return {name: 1 if i < boundary else 2 for i, name in enumerate(names)}

def dataset_hash(rows: list[dict]) -> str:
    """Отпечаток набора чанков — чтобы проверить, что Chroma и Postgres содержат один и тот же снимок."""
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def golden_for_rows(golden: list[dict], rows: list[dict], require_all=False) -> list[dict]:
    """Оставляет из golden только вопросы, чей документ реально есть в текущем снимке."""
    names = {r["filename"] for r in rows}
    missing = {g["doc"] for g in golden} - names
    if require_all and missing:
        raise ValueError("golden ссылается на отсутствующие документы: " + ", ".join(sorted(missing)))
    return [g for g in golden if g["doc"] in names]

def is_hit(result: dict, gold: dict) -> bool:
    """Попадание: тот же файл, что ожидался, и в тексте чанка есть обязательная фраза."""
    return result["filename"] == gold["doc"] and gold["must"].lower() in result["text"].lower()

def evaluate(name: str, search, golden: list[dict], k_max: int = 5, repeats: int = 3) -> dict:
    """Прогоняет один ретривер по golden-вопросам: сначала warmup вне таймера, потом repeats честных
    повторов, из которых считаются медиана/p95 латентности и Hit@k/MRR по первому повтору.
    Общая для дня 2 (Chroma) и дня 3 (pgvector) — метрики и формат таблицы должны совпадать."""
    if not golden or repeats < 1 or k_max < max(KS):
        raise ValueError("нужны вопросы, repeats >= 1 и k_max >= 5")
    warm_t0 = time.perf_counter()
    for g in golden:
        search(g["q"], k_max)  # модель, соединения и query-cache вне steady-state таймера
    warmup_ms = 1000 * (time.perf_counter() - warm_t0)
    ranks, latencies = [], []
    for repeat in range(repeats):
        for g in golden:
            t0 = time.perf_counter()
            results = search(g["q"], k_max)
            latencies.append(1000 * (time.perf_counter() - t0))
            if repeat == 0:
                ranks.append(next((pos + 1 for pos, r in enumerate(results) if is_hit(r, g)), None))
    row = {"retriever": name, "latency_ms": median(latencies),
           "p95_ms": sorted(latencies)[math.ceil(.95 * len(latencies)) - 1],
           "warmup_ms": warmup_ms, "samples": len(latencies)}
    # Ключи recall@k оставлены для совместимости адаптеров; здесь это Hit@k, не общий recall.
    for k in KS:
        row[f"recall@{k}"] = sum(r is not None and r <= k for r in ranks) / len(ranks)
    row["mrr"] = mean(1.0 / r if r else 0.0 for r in ranks)  # MRR@k_max
    row["misses"] = [g["q"] for g, r in zip(golden, ranks) if r is None]
    return row
