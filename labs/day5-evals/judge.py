# ~/proj/ai-labs/day5-evals/judge.py
"""Свой судья с рубрикой «правильность по эталону», плюс проверка согласия с твоей ручной разметкой."""
import json
from pathlib import Path

import labkit
from langfuse import get_client
from openai import OpenAI
from pydantic import BaseModel, Field

# --- НАСТРОЙКИ ---
RUN_FILE = ".local/run-hybrid-v1.json"     # какой прогон experiment.py оценивать

BASE_URL = labkit.env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
JUDGE = labkit.env("JUDGE_MODEL", required=True)
client = OpenAI(base_url=BASE_URL, api_key=labkit.env("OPENROUTER_API_KEY", required=True), timeout=60)
langfuse = get_client()

RUBRIC = """Ты судья качества ответа службы поддержки. Сравни ОТВЕТ с ЭТАЛОНОМ.
Оценка: 2 — все ключевые факты эталона присутствуют и нет противоречий; 1 — часть фактов есть, противоречий нет;
0 — ключевые факты отсутствуют или есть противоречие эталону. Честный отказ при отсутствии ответа в эталоне = 2.
Сначала напиши обоснование в одно предложение, потом оценку."""


class Verdict(BaseModel):
    reasoning: str = Field(description="Одно предложение: что совпало, что нет")
    score: int = Field(ge=0, le=2)


def judge(question: str, answer: str, reference: str) -> Verdict:
    r = client.chat.completions.create(
        model=JUDGE, temperature=0, max_tokens=300,
        response_format={"type": "json_schema", "json_schema": {"name": "verdict", "schema": Verdict.model_json_schema()}},
        messages=[{"role": "system", "content": RUBRIC}, {"role": "user", "content": f"ВОПРОС: {question}\nЭТАЛОН: {reference}\nОТВЕТ: {answer}"}],
    )
    return Verdict.model_validate_json(r.choices[0].message.content)


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    path = here / RUN_FILE
    rows = [r for r in json.loads(path.read_text(encoding="utf-8")) if r.get("reference")]
    manual_path = here / ".local" / "manual_labels.json"
    manual = json.loads(manual_path.read_text(encoding="utf-8")) if manual_path.exists() else {}
    agree, total = 0, 0
    for r in rows:
        v = judge(r["question"], r["answer"], r["reference"])
        langfuse.create_score(trace_id=r["trace_id"], name="correctness_judge", value=v.score / 2, comment="Synthetic rubric v1")
        mark = ""
        if r["question"] in manual:
            total += 1
            agree += int(manual[r["question"]] == v.score)
            mark = f" | человек: {manual[r['question']]}"
        print(f"{v.score} | {r['question'][:60]} | {v.reasoning[:80]}{mark}")
    langfuse.flush()
    if total:
        print(f"\nсогласие судьи с ручной разметкой: {agree}/{total}")
