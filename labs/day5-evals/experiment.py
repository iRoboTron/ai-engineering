# ~/proj/ai-labs/day5-evals/experiment.py
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from langfuse import get_client
from rag_pipeline import HERE, rag
from common import load_golden

OUTPUT = HERE / ".local"


def ensure_dataset() -> str:
    if os.getenv("EVAL_EXPORT_SYNTHETIC") != "1":
        raise RuntimeError("Экспорт текстов требует EVAL_EXPORT_SYNTHETIC=1; сначала проверь, что набор учебный")
    golden = load_golden()
    serialized = json.dumps(golden, ensure_ascii=False, sort_keys=True)
    name = "golden-rag-" + hashlib.sha256(serialized.encode()).hexdigest()[:12]
    client = get_client()
    # API v3: create_dataset — create-or-update; стабильные item ids не дублируют вопросы.
    client.create_dataset(name=name, description="Synthetic fixture; versioned by content hash")
    for index, g in enumerate(golden):
        item_id = hashlib.sha256(f"{name}:{index}".encode()).hexdigest()
        client.create_dataset_item(id=item_id, dataset_name=name,
            input={"question": g["q"]},
            expected_output={"doc": g["doc"], "must": g["must"], "reference": g.get("reference"), "unanswerable": g.get("unanswerable", False)})
    return name


def run(dataset: str, mode: str, name: str) -> list[dict]:
    rows = []
    for item in get_client().get_dataset(dataset).items:
        with item.run(run_name=name, run_metadata={"mode": mode}) as root:
            output = rag(item.input["question"], mode)
            expected = item.expected_output
            hit = any(filename == expected["doc"] and expected["must"].lower() in text.lower()
                      for filename, text in zip(output["filenames"], output["contexts"])) if expected["doc"] else False
            root.score_trace(name="retrieval_hit", value=float(hit))
            rows.append({"trace_id": root.trace_id, "question": item.input["question"],
                         "answer": output["answer"], "needs_contact": output["needs_contact"],
                         "contexts": output["contexts"], "reference": expected.get("reference"),
                         "unanswerable": expected.get("unanswerable", False), "hit": hit})
    get_client().flush()
    return rows


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "hybrid_rerank"
    name = sys.argv[2] if len(sys.argv) > 2 else f"{mode}-v1"
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError("Имя прогона: только буквы, цифры, _ и -")
    dataset = ensure_dataset()
    rows = run(dataset, mode, name)
    if not rows:
        raise RuntimeError("Пустой датасет")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / f"run-{name}.json"
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{dataset}: {len(rows)} вопросов; локальный отчёт {path}")
