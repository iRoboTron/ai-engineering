# ~/proj/ai-labs/day1-llm-basics/02_structured.py
import json
import re
import sys
from typing import Literal

import labkit                       # читает .env, даёт пути DATA и OUT
from openai import BadRequestError  # ошибка 400 от провайдера
from pydantic import BaseModel, ConfigDict, Field, model_validator   # Pydantic: описание и проверка формы данных

from client import make_client, MODEL

# --- НАСТРОЙКИ ---
INPUT_DIR = labkit.DATA / "vacancies"       # сюда положи тексты вакансий: 01.txt, 02.txt, 03.txt
OUT_DIR = labkit.out_dir("day1")            # результат: out/day1/<имя файла>.json


class Vacancy(BaseModel):
    """Какие поля хотим получить из текста вакансии. Из этого класса строится JSON-схема для модели."""
    model_config = ConfigDict(extra="forbid")                                    # лишние поля запрещены
    title: str = Field(description="Название позиции как в тексте")              # description видит модель
    company: str = Field(description="Компания или unknown")                     # компания или "unknown"
    seniority: Literal["junior", "middle", "senior", "unknown"]                  # уровень, только из списка
    must_have: list[str]                                                         # обязательные требования
    nice_to_have: list[str]                                                      # желательные требования
    salary_min: int | None = Field(description="Нижняя граница в рублях или null")   # нижняя граница ЗП
    salary_max: int | None = Field(description="Верхняя граница в рублях или null")  # верхняя граница ЗП
    remote: bool | None                                                          # удалёнка: true / false / null

    @model_validator(mode="after")                    # проверка после заполнения всех полей
    def check_salary(self):
        if any(v is not None and v < 0 for v in (self.salary_min, self.salary_max)):
            raise ValueError("зарплата не может быть отрицательной")
        if self.salary_min is not None and self.salary_max is not None and self.salary_min > self.salary_max:
            raise ValueError("нижняя граница зарплаты выше верхней")
        return self


SYSTEM = "Ты извлекаешь структурированные данные из текста вакансии. Отвечай только JSON по схеме, без пояснений и без markdown."
FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.S)   # срезает ```json ... ``` если модель обернула ответ


def extract(client, text: str) -> Vacancy:
    """Текст вакансии → объект Vacancy. Сначала строгий режим json_schema, при отказе провайдера — запасной."""
    schema = Vacancy.model_json_schema()                  # Pydantic-класс → JSON Schema
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}]
    try:
        r = client.chat.completions.create(
            model=MODEL,
            temperature=0,                                # извлечение данных: без случайности
            max_tokens=600,
            response_format={"type": "json_schema", "json_schema": {"name": "vacancy", "strict": True, "schema": schema}},  # провайдер ограничивает вывод схемой
            messages=messages,
        )
        mode = "json_schema"
    except BadRequestError as exc:
        # Не маскируем auth/rate limit/сетевые ошибки и произвольные 400.
        if not any(word in str(exc).lower() for word in ("json_schema", "response_format", "structured output")):
            raise
        print(f"  json_schema не прошёл ({type(exc).__name__}), запасной путь через промпт", file=sys.stderr)
        messages[0]["content"] += "\nСхема JSON:\n" + json.dumps(schema, ensure_ascii=False)   # схема текстом в промпт
        r = client.chat.completions.create(model=MODEL, temperature=0, max_tokens=600, messages=messages)
        mode = "prompt+validate"
    if not r.choices or not r.choices[0].message.content or r.choices[0].finish_reason == "length":
        raise RuntimeError("structured output отсутствует/оборван; отказ или лимит не считается успешным JSON")
    raw = FENCE.sub("", r.choices[0].message.content.strip())
    vacancy = Vacancy.model_validate_json(raw)            # проверка той же схемой; ошибка не замалчивается
    print(f"  режим: {mode}, usage={r.usage}")
    return vacancy


if __name__ == "__main__":
    files = sorted(INPUT_DIR.glob("*.txt"))
    if not files:
        raise SystemExit(f"Нет файлов *.txt в {INPUT_DIR}: сохрани туда тексты вакансий (шаг 1 лабы)")
    client = make_client()
    for path in files:
        print(f"\n{path.name}")
        v = extract(client, path.read_text(encoding="utf-8"))
        (OUT_DIR / f"{path.stem}.json").write_text(v.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")  # объект → JSON-файл
        print(f"  {v.title} @ {v.company} [{v.seniority}] must={len(v.must_have)} remote={v.remote}")
    print(f"\nJSON сохранены в {OUT_DIR}")
