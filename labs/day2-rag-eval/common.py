# ~/proj/ai-labs/day2-rag-eval/common.py
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT.parent / "fixtures"

def snapshot_path(collection: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{2,63}", collection):
        raise ValueError("collection: 3–64 буквы, цифры, дефис или подчёркивание")
    return ROOT / ".local" / collection

def load_config(collection: str) -> dict:
    return json.loads((snapshot_path(collection) / "config.json").read_text(encoding="utf-8"))

def load_rows(collection: str) -> list[dict]:
    return [json.loads(line) for line in (snapshot_path(collection) / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

def load_golden(path=None) -> list[dict]:
    source = Path(path) if path else FIXTURES / "golden.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows or any(not all(isinstance(r.get(k), str) and r[k].strip() for k in ("q", "doc", "must")) for r in rows):
        raise ValueError("golden: требуется непустой список q/doc/must")
    return rows

def tenant_map(filenames) -> dict[str, int]:
    names = sorted(set(filenames))
    if len(names) < 2:
        raise ValueError("для сравнения tenant нужны минимум два документа")
    boundary = (len(names) + 1) // 2
    return {name: 1 if i < boundary else 2 for i, name in enumerate(names)}

def dataset_hash(rows: list[dict]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def golden_for_rows(golden: list[dict], rows: list[dict], require_all=False) -> list[dict]:
    names = {r["filename"] for r in rows}
    missing = {g["doc"] for g in golden} - names
    if require_all and missing:
        raise ValueError("golden ссылается на отсутствующие документы: " + ", ".join(sorted(missing)))
    return [g for g in golden if g["doc"] in names]
