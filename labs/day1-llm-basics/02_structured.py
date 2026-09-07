# ~/proj/ai-labs/day1-llm-basics/02_structured.py
import json
import re
import sys
from pathlib import Path

from typing import Literal
from openai import BadRequestError
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from client import make_client, MODEL


class Vacancy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(description="Название позиции как в тексте")
    company: str = Field(description="Компания или unknown")
    seniority: Literal["junior", "middle", "senior", "unknown"]
    must_have: list[str]
    nice_to_have: list[str]
    salary_min: int | None = Field(description="Нижняя граница в рублях или null")
    salary_max: int | None = Field(description="Верхняя граница в рублях или null")
    remote: bool | None

    @model_validator(mode="after")
    def check_salary(self):
        if any(v is not None and v < 0 for v in (self.salary_min, self.salary_max)):
            raise ValueError("зарплата не может быть отрицательной")
        if self.salary_min is not None and self.salary_max is not None and self.salary_min > self.salary_max:
            raise ValueError("нижняя граница зарплаты выше верхней")
        return self


SYSTEM = "Ты извлекаешь структурированные данные из текста вакансии. Отвечай только JSON по схеме, без пояснений и без markdown."
FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.S)


def extract(client, text: str) -> Vacancy:
    schema = Vacancy.model_json_schema()
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}]
    try:
        r = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            max_tokens=600,
            response_format={"type": "json_schema", "json_schema": {"name": "vacancy", "strict": True, "schema": schema}},
            messages=messages,
        )
        mode = "json_schema"
    except BadRequestError as exc:
        # Не маскируем auth/rate limit/сетевые ошибки и произвольные 400.
        if not any(word in str(exc).lower() for word in ("json_schema", "response_format", "structured output")):
            raise
        print(f"  json_schema не прошёл ({type(exc).__name__}), запасной путь через промпт", file=sys.stderr)
        messages[0]["content"] += "\nСхема JSON:\n" + json.dumps(schema, ensure_ascii=False)
        r = client.chat.completions.create(model=MODEL, temperature=0, max_tokens=600, messages=messages)
        mode = "prompt+validate"
    if not r.choices or not r.choices[0].message.content or r.choices[0].finish_reason == "length":
        raise RuntimeError("structured output отсутствует/оборван; отказ или лимит не считается успешным JSON")
    raw = FENCE.sub("", r.choices[0].message.content.strip())
    vacancy = Vacancy.model_validate_json(raw)  # ValidationError не замалчивается и не публикуется как успех
    print(f"  режим: {mode}, usage={r.usage}")
    return vacancy


if __name__ == "__main__":
    client = make_client()
    if len(sys.argv) < 2:
        raise SystemExit("передай пути к публичным текстам вакансий")
    out = Path(__file__).resolve().parent / "out"
    out.mkdir(exist_ok=True)
    for path in map(Path, sys.argv[1:]):
        print(f"\n{path.name}")
        v = extract(client, path.read_text(encoding="utf-8"))
        (out / f"{path.stem}.json").write_text(v.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {v.title} @ {v.company} [{v.seniority}] must={len(v.must_have)} remote={v.remote}")
