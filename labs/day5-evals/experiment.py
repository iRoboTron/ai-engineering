# ~/proj/ai-labs/day5-evals/experiment.py
"""Прогоняет весь golden-набор через rag_pipeline и записывает трейсы как один именованный прогон в Langfuse."""
import hashlib
import json
import re

import labkit
from langfuse import get_client
from rag_pipeline import HERE, rag
from common import load_golden

OUTPUT = HERE / ".local"

# --- НАСТРОЙКИ: сделай два прогона по очереди, каждый со своим именем ---
MODE = "hybrid_rerank"          # "dense" или "hybrid_rerank" — какой ретривер дня 2 использовать
RUN_NAME = "hybrid-v1"          # имя прогона в Langfuse; для второго прохода — MODE="dense", RUN_NAME="dense-v1"
EXPORT_SYNTHETIC = True         # явное подтверждение: набор вопросов учебный, публиковать в Langfuse можно


def ensure_dataset() -> str:
    if not EXPORT_SYNTHETIC:
        raise RuntimeError("Экспорт текстов требует EXPORT_SYNTHETIC = True; сначала проверь, что набор учебный")
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
    if not re.fullmatch(r"[A-Za-z0-9_-]+", RUN_NAME):
        raise ValueError("RUN_NAME: только буквы, цифры, _ и -")
    dataset = ensure_dataset()
    rows = run(dataset, MODE, RUN_NAME)
    if not rows:
        raise RuntimeError("Пустой датасет")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / f"run-{RUN_NAME}.json"
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{dataset}: {len(rows)} вопросов; локальный отчёт {path}")
