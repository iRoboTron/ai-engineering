# День 1. Лаба: вакансии и первые запросы к LLM

## Результат

Два артефакта. Первый — `career/vacancies-2026-09.md`: таблица из 20 реальных вакансий с подсчётом требований; она заземляет карту профессии из главы 1 и станет основой резюме. Второй — публичный репозиторий портфолио `~/proj/ai-labs/` с папкой `day1-llm-basics/`: пять рабочих ноутбуков и `results.md` с измеренными числами (токены RU против EN, TTFT, стоимость сценария для двух моделей). Это первый код, который увидит работодатель, поэтому пишем аккуратно.

## Карта лабы

```mermaid
flowchart LR
    HH["hh.ru\n20 вакансий"] --> VAC["career/vacancies-2026-09.md\nтоп-10 требований"]
    HH --> TXT["3 текста вакансий\nai-labs/data/vacancies/*.txt"]
    CL["client.py\nOpenRouter через socks5"] --> S1["01 usage, temperature\nтокены RU/EN"]
    CL --> S2["02 structured output\nPydantic + json_schema"]
    CL --> S3["03 streaming\nTTFT, tok/s"]
    CL --> S4["04 стоимость\nпрайс из /models"]
    CL --> S5["05 ретраи\nbackoff + джиттер"]
    TXT --> S2
    S1 --> RES["results.md\nчисла и выводы"]
    S2 --> RES
    S3 --> RES
    S4 --> RES
    S5 --> RES
    VAC --> CV["Резюме v1\nна hh.ru"]
    RES --> CV

    style HH fill:#2d2d2d,color:#fff
    style VAC fill:#7d6608,color:#fff
    style TXT fill:#7d6608,color:#fff
    style CL fill:#4a235a,color:#fff
    style S1 fill:#1a5276,color:#fff
    style S2 fill:#1a5276,color:#fff
    style S3 fill:#1a5276,color:#fff
    style S4 fill:#1a5276,color:#fff
    style S5 fill:#1a5276,color:#fff
    style RES fill:#1e8449,color:#fff
    style CV fill:#1e8449,color:#fff
```

## Подготовка

Что нужно до старта (15 минут):

- Python 3.12 и `venv`. Ключ OpenRouter — отдельный учебный с ограниченным бюджетом, не продовый; создай его на с `openrouter.ai/keys`.
- Доступ к OpenRouter из РФ блокируется по IP (ты это видел 3 сентября: `403 Access denied by security policy`). Решение то же, что для Hermes: socks5-прокси через LXC 106 на kl-pc. Библиотеке `httpx`, на которой работает `openai`, нужен extra `socks`.
- Аккаунт на hh.ru с пустым или старым резюме — сегодня появится новое.

```bash
# Из корня репозитория курса; отличающиеся существующие файлы не перезаписываются.
python3 scripts/install_labs.py --dest ~/proj/ai-labs
cd ~/proj/ai-labs
git init -q
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --require-hashes -r requirements.txt
# Делает labkit.py видимым для import из любой папки дня и из VS Code — без этой строки
# `import labkit` работает только если явно возиться с sys.path в каждом файле.
echo "$(pwd)" > "$(python -c 'import site; print(site.getsitepackages()[0])')/ai_labs.pth"
cd day1-llm-basics
```

Установщик копирует готовые исходники, публичные fixtures и безопасный .gitignore: .env, .local/, corpus/, chroma/, out/ и локальные виртуальные окружения не публикуются. Не заменяй существующий .gitignore вслепую. Все команды Python дня 1 выполняй из day1-llm-basics; ниже разбирается уже установленный код.

Строка с `ai_labs.pth` — разовая настройка окружения, а не часть кода лабы: Python при старте читает файлы
`*.pth` в `site-packages` интерпретатора и добавляет перечисленные в них пути в `sys.path`. Так `import labkit`
работает откуда угодно — из терминала, из VS Code, из отладчика — без явного `sys.path.insert` в каждом
скрипте. Если создашь venv заново, повтори эту строку.

Переменные окружения — в файле `~/proj/ai-labs/.env` (он в `.gitignore`). Содержимое:

```bash
export OPENROUTER_API_KEY="sk-or-..."
# платная, но без режима рассуждений и с json_schema/tools; день 1 стоит центы.
# Модели с суффиксом :free стоят в общей очереди (429), а «думающие» модели тратят max_tokens на скрытые рассуждения
export LLM_MODEL="anthropic/claude-haiku-4.5"
# прокси нужен только из РФ; убери, если запускаешь там, где OpenRouter доступен напрямую
# socks5h, а не socks5: имена резолвит прокси, а не локальный DNS провайдера
export HTTPS_PROXY="socks5h://192.168.0.106:1080"
export https_proxy="$HTTPS_PROXY"
```

Загрузка и проверка доступа:

```bash
source ~/proj/ai-labs/.env
curl -sS -o /dev/null -w '%{http_code}\n' https://openrouter.ai/api/v1/models
```

Ожидаемо `200`. При `403` проверь условия доступа провайдера и сетевой маршрут; код сам по себе не доказывает, что прокси не применился. `curl` читает `https_proxy` в нижнем регистре, `httpx` — в любом, поэтому в файле заданы оба. Модель по умолчанию взята из конфига web-agent; любую другую подставишь через `LLM_MODEL`, список — `openrouter.ai/models`.

### labkit: один файл вместо параметров командной строки

Все дни этой недели используют общий модуль `labkit.py`. Он делает две вещи: читает `.env` сам, без
`source`, и определяет пути `labkit.DATA`, `labkit.OUT`, `labkit.FIXTURES`, одинаковые для всех дней.
Каждый скрипт лабы начинается с `import labkit` — после этого ключ, модель и прокси уже в окружении
процесса, а результаты и входные файлы всегда лежат в одном и том же месте. Все настройки, которые
раньше были бы флагами командной строки (какую модель взять, какой файл обработать, сколько раз
повторить), в этой серии — именованные константы в начале файла: меняешь значение, сохраняешь, нажимаешь
Run. Вводить ничего в консоли не нужно.

```python
# ~/proj/ai-labs/labkit.py
"""Общий вход для всех лаб: читает .env и задаёт пути.

Первая строка каждого скрипта — `import labkit`. После этого ключи и модель из .env
уже в переменных окружения, а пути к данным одинаковы во всех днях.
"""
import os                     # доступ к переменным окружения
import sys                    # список путей, где Python ищет модули
from pathlib import Path      # объектные пути к файлам вместо строк

ROOT = Path(__file__).resolve().parent   # папка проекта ~/proj/ai-labs
ENV_FILE = ROOT / ".env"                 # ключи и настройки (в git не попадает)
DATA = ROOT / "data"                     # твои входные файлы: вакансии, документы, разметка
OUT = ROOT / "out"                       # результаты запусков, по папке на день
LOCAL = ROOT / ".local"                  # кэши и снимки индексов; не публикуется
FIXTURES = ROOT / "fixtures"             # учебные публичные данные из курса


def load_env(path: Path = ENV_FILE) -> int:
    """Читает строки вида KEY=value и export KEY="value". Уже заданные переменные не перезаписывает."""
    if not path.is_file():                                  # .env ещё не создан — работаем без него
        return 0
    loaded = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:   # пустые строки и комментарии
            continue
        if line.startswith("export "):                            # форма для source в терминале
            line = line[len("export "):]
        key, value = (part.strip() for part in line.split("=", 1))
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]                                   # снимаем кавычки
        value = os.path.expandvars(value)                         # https_proxy="$HTTPS_PROXY" → подстановка
        if key and key not in os.environ:
            os.environ[key] = value
            loaded += 1
    return loaded


def env(name: str, default: str | None = None, *, required: bool = False) -> str | None:
    """Переменная из окружения или .env. required=True даёт понятную ошибку вместо KeyError."""
    value = os.environ.get(name, default)
    if required and not value:
        raise SystemExit(f"Нет переменной {name}: добавь строку {name}=... в {ENV_FILE} (образец — .env.example)")
    return value


def out_dir(day: str) -> Path:
    """Папка результатов дня, например out/day1. Создаётся при первом обращении."""
    path = OUT / day
    path.mkdir(parents=True, exist_ok=True)
    return path


def use_day(name: str) -> Path:
    """Делает модули другого дня видимыми для импорта: labkit.use_day("day2-rag-eval"); потом from common import ...."""
    path = ROOT / name
    if not path.is_dir():
        raise SystemExit(f"Нет папки {path}: сначала установи лабы курса")
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
    return path


load_env()                                # выполняется один раз при первом import labkit
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))            # корень проекта виден для импортов из любого дня
```

Настрой интерпретатор VS Code один раз на весь проект — дальше он не спрашивается снова:

<!-- lab: .vscode/settings.json -->
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.terminal.activateEnvironment": true
}
```

Открой папку `~/proj/ai-labs` в VS Code (`code ~/proj/ai-labs` или «Файл → Открыть папку»). После этого
любой `.py`-файл запускается кнопкой ▶ Run в правом верхнем углу или `F5` — без терминала, без активации
окружения руками, без аргументов. Всё окружение недели — один `.venv` в корне `ai-labs`, тот же, что ты
создал только что; отдельного окружения на каждый день нет и не нужно: зависимости всех семи дней уже
зафиксированы в одном `requirements.txt`.

Часть скриптов — обычные `.py`-файлы (их импортируют другие файлы: `client.py`, `common.py` и подобные —
запускать напрямую их не нужно). Остальные, которые ты и должен запускать каждый день, — ноутбуки `.ipynb`:
код разбит на ячейки, выполняются сверху вниз кнопкой ▶ Run All на панели ноутбука, промежуточные
результаты видно между ячейками, не только в самом низу консоли. Для этого нужно расширение **Jupyter**
в VS Code (одно на всё, ставится один раз через маркетплейс расширений); ядро (kernel) выбери тем же
`.venv`, что ты только что создал, — VS Code предложит его сам при первом открытии ноутбука.

Полный список переменных недели — в одном файле-образце, чтобы не искать по главам, какая переменная
для какого дня. Не редактируй его напрямую: скопируй в `.env` и впиши свои значения, `.env` в `.gitignore`,
`.env.example` — нет, это справочник, в нём не должно быть настоящих ключей.

```bash
# ~/proj/ai-labs/.env.example
# Скопируй в .env и заполни: cp .env.example .env
# День 1 — обязательно с самого начала
export OPENROUTER_API_KEY="sk-or-..."
export LLM_MODEL="anthropic/claude-haiku-4.5"
export HTTPS_PROXY="socks5h://192.168.0.106:1080"    # нужен только из РФ; убери, если провайдер доступен напрямую
export https_proxy="$HTTPS_PROXY"
# export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"   # обычно не нужно менять
# export LLM_MODEL_CHEAP="deepseek/deepseek-v4-flash-0731"    # день 1, шаг 6: с чем сравнивать по цене

# День 3 — после первого запуска docker-compose (шаг 1 главы 2 дня 3, генерируется один раз)
# export PG_ADMIN_PASSWORD="..."
# export PG_APP_PASSWORD="..."
# export PG_ADMIN_DSN="postgresql://rag_admin:$PG_ADMIN_PASSWORD@127.0.0.1:5433/rag"
# export PG_DSN="postgresql://rag_app:$PG_APP_PASSWORD@127.0.0.1:5433/rag"

# День 4 — опционально, только для удалённого сервиса памяти (по умолчанию локальный JSON, без этих строк)
# export MEMORY_URL="http://100.69.146.20:443"
# export MEMORY_REMOTE_PROJECT="ai-labs"

# День 5 — после регистрации в своём Langfuse (шаг 1 главы 2 дня 5)
# export LANGFUSE_PUBLIC_KEY="pk-lf-..."
# export LANGFUSE_SECRET_KEY="sk-lf-..."
# export LANGFUSE_HOST="http://127.0.0.1:3000"
# export JUDGE_MODEL="anthropic/claude-haiku-4.5"    # день 5 (судья) и день 6 (не используется), независим от LLM_MODEL

# День 6 — опционально, по числу пройденных шагов
# export OLLAMA_URL="http://127.0.0.1:11434"
# export YC_FOLDER_ID="..."          # каталог Yandex Cloud, для ru_provider.py
# export YC_API_KEY="..."
# export WA_URL="http://127.0.0.1:8000"      # тестовый staging web-agent для red_team.py
# export WA_WIDGET_TOKEN="..."
```

## Шаг 1. Двадцать вакансий (30 минут, без кода)

Открой hh.ru и по очереди поищи: «AI инженер», «LLM инженер», «ML инженер LLM», «разработчик AI агентов», «RAG», «Python LLM». Отбери 20 вакансий, которые ты бы реально рассматривал (уровень middle или «без указания», Python, удалёнка или твой город). По каждой заполни строку таблицы в `~/Documents/lessons/ai-engineering/career/vacancies-2026-09.md`:

```markdown
| # | Компания | Название | Зарплата | Обязательно | Желательно | Есть у меня | Ссылка |
|---|---|---|---|---|---|---|---|
| 1 | … | AI-инженер | 250–350k | Python, RAG, LangChain, pgvector, FastAPI | Langfuse, vLLM | Python, RAG, FastAPI, Postgres | … |
```

Затем внизу файла — подсчёт: сколько раз встретилось каждое требование. Двадцать вакансий дадут честную картину: что в топе, чего у тебя нет, какие слова обязаны быть в резюме. Три вакансии с самым подробным текстом сохрани целиком в `~/proj/ai-labs/data/vacancies/01.txt`, `02.txt`, `03.txt` — они пойдут в шаг 4 (это входные данные лабы, они лежат рядом с кодом, а не в отдельном репозитории career).

Не пропускай этот шаг ради кода: он определяет, какими словами ты вечером напишешь резюме.

## Шаг 2. Общий клиент

Все скрипты используют один клиент, чтобы прокси, таймауты и заголовки настраивались в одном месте. `max_retries=0` — ретраи мы напишем сами в шаге 7 и хотим видеть ошибки, а не скрывать их.

```python
# ~/proj/ai-labs/day1-llm-basics/client.py
import labkit                 # читает .env: ключ, модель, прокси
from openai import OpenAI     # официальный клиент OpenAI; OpenRouter говорит на том же протоколе

# --- НАСТРОЙКИ (общие для всех скриптов дня 1) ---
BASE_URL = labkit.env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")   # адрес API
MODEL = labkit.env("LLM_MODEL", "anthropic/claude-haiku-4.5")                  # модель по умолчанию


def make_client(timeout: float = 60.0) -> OpenAI:
    """Создаёт клиент. Прокси из HTTPS_PROXY библиотека httpx подхватывает сама."""
    api_key = labkit.env("OPENROUTER_API_KEY", required=True)   # без ключа — понятная ошибка, а не тихий 401
    return OpenAI(
        base_url=BASE_URL,      # куда слать запросы
        api_key=api_key,        # заголовок Authorization
        timeout=timeout,        # секунд на один запрос
        max_retries=0,          # повторы делаем сами (шаг 7), чтобы их видеть
        default_headers={       # OpenRouter показывает эти поля в статистике приложений
            "HTTP-Referer": "https://ai-engineering.adelfos.ru",
            "X-Title": "ai-labs day1",
        },
    )
```

Проверка: `python -c "from client import make_client; print(make_client().models.list().data[0].id)"` печатает id какой-нибудь модели. Заголовки `HTTP-Referer` и `X-Title` — рекомендация OpenRouter для статистики, на работу не влияют.

## Шаг 3. Запрос, usage и temperature

Три вещи за один скрипт: как выглядит ответ и `usage`, как temperature меняет разброс, и сколько токенов занимает одинаковая фраза на русском и английском.

```python
# ~/proj/ai-labs/day1-llm-basics/01_basics.py
import labkit  # noqa: F401  читает .env
from client import make_client, MODEL

# --- НАСТРОЙКИ ---
QUESTION = "Придумай название для сервиса, который отвечает на вопросы по документам компании."
TEMPERATURES = (0.0, 1.0)     # 0 — почти детерминированно, 1 — разнообразно
REPEATS = 3                   # сколько раз задать один вопрос при каждой температуре
SAMPLES = (                   # пара фраз одинакового смысла для сравнения токенов
    "The quick brown fox jumps over the lazy dog near the river.",
    "Быстрая рыжая лиса перепрыгивает через ленивую собаку у реки.",
)

client = make_client()


def ask(prompt: str, temperature: float):
    """Один запрос к модели. Возвращает текст ответа и usage — счётчики токенов."""
    r = client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        max_tokens=120,                                   # потолок длины ответа
        messages=[
            {"role": "system", "content": "Отвечай одним коротким предложением, без пояснений."},  # правила
            {"role": "user", "content": prompt},                                                    # вопрос
        ],
    )
    if not r.choices or not r.choices[0].message.content or r.usage is None:
        raise RuntimeError("нет текста/usage: проверь отказ, лимит ответа и возможности провайдера")
    return r.choices[0].message.content.strip(), r.usage


print(f"модель: {MODEL}")
for t in TEMPERATURES:
    print(f"\n=== temperature={t} ===")
    for i in range(REPEATS):
        text, usage = ask(QUESTION, t)
        print(f"{i + 1}. {text}   [in={usage.prompt_tokens} out={usage.completion_tokens}]")   # in — токены запроса, out — ответа

print("\n=== токены: русский против английского ===")
for s in SAMPLES:
    r = client.chat.completions.create(model=MODEL, max_tokens=1, messages=[{"role": "user", "content": s}])  # ответ не нужен, нужен подсчёт входа
    print(f"{r.usage.prompt_tokens:4d} токенов | {len(s):3d} символов | {s}")
```

Что должно получиться: при `temperature=0.0` три ответа одинаковые или почти одинаковые, при `1.0` — заметно разные. Числа токенов для RU и EN могут различаться в любую сторону; соотношение зависит от токенизатора модели, поэтому запиши обе цифры в `results.md`. В `prompt_tokens` входят служебные токены разметки сообщения — это нормально.

## Шаг 4. Structured output: вакансия → объект

Берём три текста вакансий из шага 1 и превращаем их в Pydantic-объекты. Схема — из модели, режим — `json_schema`, при отказе провайдера — запасной путь через промпт со схемой. В обоих случаях ответ проходит `model_validate_json`.

```python
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
```

Запуск: открой `02_structured.ipynb` в VS Code и нажми ▶ Run All — файл сам находит все `*.txt` в `~/proj/ai-labs/data/vacancies/`. Три JSON-файла появятся в `out/day1/`, в консоли — режим (`json_schema` или запасной) и токены. Если в `stderr` каждый раз запасной путь — модель не поддерживает structured outputs через OpenRouter; выбери на `openrouter.ai/models` модель с фильтром «Structured Outputs» и поставь другую `LLM_MODEL` в `.env`. Оба варианта — легитимный результат для `results.md`: на собеседовании ценят именно понимание, что запасной путь обязателен.

## Шаг 5. Streaming: время до первого токена

```python
# ~/proj/ai-labs/day1-llm-basics/03_streaming.py
import time

import labkit  # noqa: F401  читает .env
from client import make_client, MODEL

# --- НАСТРОЙКИ ---
PROMPT = "Объясни в пяти предложениях, что такое RAG, для DevOps-инженера."
MAX_TOKENS = 300

client = make_client()
t0 = time.perf_counter()      # момент отправки запроса
first = None                  # момент первого токена (для TTFT)
usage = None                  # счётчики токенов, приходят в последнем чанке

stream = client.chat.completions.create(
    model=MODEL,
    stream=True,                                  # ответ приходит кусками, а не целиком
    stream_options={"include_usage": True},       # попросить usage в конце стрима
    max_tokens=MAX_TOKENS,
    messages=[{"role": "user", "content": PROMPT}],
)
for event in stream:                              # каждый event — один кусок ответа
    if event.usage:
        usage = event.usage                       # последний чанк: только usage, без текста
    if not event.choices:
        continue
    delta = event.choices[0].delta.content or ""  # новые символы в этом куске
    if delta and first is None:
        first = time.perf_counter()               # первый токен пришёл
    print(delta, end="", flush=True)              # печатаем сразу, как чат в браузере

t1 = time.perf_counter()
if first is None:
    raise RuntimeError("стрим не содержал текста: проверь отказ и finish_reason")
print(f"\n\nTTFT: {first - t0:.2f}s | всего: {t1 - t0:.2f}s", end="")     # TTFT — время до первого токена
if usage and first:
    print(f" | out={usage.completion_tokens} → {max(0, usage.completion_tokens - 1) / max(t1 - first, 1e-9):.1f} tok/s")  # скорость генерации
else:
    print(" | usage в стриме не пришёл — провайдер не поддерживает include_usage")
```

Запусти три раза и запиши медиану TTFT и tok/s. Через socks5-прокси в Казахстан TTFT будет выше, чем «из мира», — это тоже число для отчёта и хороший разговор про латентность в условиях РФ.

## Шаг 6. Стоимость по прайсу провайдера

OpenRouter отдаёт цены за токен в `GET /api/v1/models`. Считаем стоимость типичного RAG-запроса (3500 токенов на входе, 400 на выходе) для месяца с тысячей запросов в день и сравниваем твою модель с дешёвой. Файл уже сравнивает с `deepseek/deepseek-v4-flash-0731`; хочешь другую — впиши её в `CHEAP_MODEL` из списка, который печатает скрипт, и запусти снова.

```python
# ~/proj/ai-labs/day1-llm-basics/04_cost.py
import httpx
import labkit

from client import BASE_URL, MODEL

# --- НАСТРОЙКИ ---
IN_TOKENS, OUT_TOKENS = 3500, 400           # типичный RAG-запрос: контекст + вопрос → короткий ответ
REQ_PER_MONTH = 1000 * 30                   # нагрузка сценария: тысяча запросов в день
CHEAP_MODEL = labkit.env("LLM_MODEL_CHEAP", "deepseek/deepseek-v4-flash-0731")  # модель для сравнения
MIN_CONTEXT = 100_000                       # фильтр для списка дешёвых моделей


def load_models() -> list[dict]:
    """Каталог моделей OpenRouter: цены, размер контекста, поддерживаемые параметры."""
    r = httpx.get(f"{BASE_URL}/models", timeout=30)  # прокси из HTTPS_PROXY подхватится сам
    r.raise_for_status()                    # исключение при HTTP-ошибке
    return r.json()["data"]


def price(models: list[dict], model_id: str) -> tuple[float, float, int | None]:
    """Цена за один токен входа и выхода (USD) и размер контекста."""
    for m in models:
        if m["id"] == model_id:
            p = m["pricing"]
            return float(p["prompt"]), float(p["completion"]), m.get("context_length")
    raise SystemExit(f"модель {model_id} не найдена в /models")


def monthly_cost(p_in: float, p_out: float) -> float:
    return (IN_TOKENS * p_in + OUT_TOKENS * p_out) * REQ_PER_MONTH


models = load_models()
cheap_candidates = sorted(                                                        # платные модели с большим контекстом
    (m for m in models if float(m["pricing"]["prompt"]) > 0 and (m.get("context_length") or 0) >= MIN_CONTEXT),
    key=lambda m: float(m["pricing"]["prompt"]),                                  # сортировка по цене входа
)[:10]
print(f"10 самых дешёвых моделей с контекстом ≥ {MIN_CONTEXT // 1000}k (цена за 1M входных токенов, USD):")
for m in cheap_candidates:
    print(f"  {float(m['pricing']['prompt']) * 1e6:8.3f}  {m['id']}")

for label, mid in (("основная", MODEL), ("дешёвая", CHEAP_MODEL)):
    p_in, p_out, ctx = price(models, mid)
    print(f"\n{label}: {mid} (контекст {ctx})")
    print(f"  вход ${p_in * 1e6:.2f}/1M, выход ${p_out * 1e6:.2f}/1M, отношение выход/вход: {p_out / p_in if p_in else None}")
    print(f"  один RAG-запрос: ${IN_TOKENS * p_in + OUT_TOKENS * p_out:.5f}")
    print(f"  {REQ_PER_MONTH} запросов в месяц: ${monthly_cost(p_in, p_out):.2f}")
```

Запиши обе месячные суммы и коэффициент «выход дороже входа». Разница между моделями в десятки раз при одинаковом сценарии — главный аргумент за роутинг моделей и за evals: дешёвая модель годится ровно там, где измеренное качество не падает.

## Шаг 7. Ретраи с backoff

Сетевые ошибки, `429 Too Many Requests` и `5xx` от провайдера — норма, и клиент обязан их переживать. Повторяем только то, что имеет смысл повторять; `400`/`404` (неверная модель, плохой запрос) повторять бессмысленно.

```python
# ~/proj/ai-labs/day1-llm-basics/05_retry.py
import random
import sys
import time

import labkit  # noqa: F401  читает .env
from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError   # ошибки, после которых есть смысл повторить

from client import make_client, MODEL

# --- НАСТРОЙКИ ---
TIMEOUT = 60.0      # секунд на запрос; поставь 0.3, чтобы увидеть ретраи по таймауту
ATTEMPTS = 5        # максимум попыток
BASE_DELAY = 1.0    # первая пауза, дальше удвоение: 1, 2, 4, 8…
MAX_DELAY = 20.0    # потолок паузы
PROMPT = "Одним предложением: зачем клиенту к LLM нужны ретраи?"

RETRYABLE = (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)   # 429, сеть, таймаут, 5xx


def with_retries(fn, attempts: int = ATTEMPTS, base: float = BASE_DELAY, cap: float = MAX_DELAY):
    """Вызывает fn(); при временной ошибке ждёт и повторяет. Exponential backoff с джиттером."""
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except RETRYABLE as exc:
            if attempt == attempts:
                raise                                                             # попытки кончились — ошибка наверх
            delay = min(cap, base * 2 ** (attempt - 1)) + random.uniform(0, 0.5)  # экспонента + случайный сдвиг
            print(f"попытка {attempt} не удалась: {type(exc).__name__}; жду {delay:.1f}s", file=sys.stderr)
            time.sleep(delay)


client = make_client(timeout=TIMEOUT)
answer = with_retries(
    lambda: client.chat.completions.create(          # lambda: сам запрос упакован в функцию без аргументов
        model=MODEL,
        max_tokens=60,
        messages=[{"role": "user", "content": PROMPT}],
    )
)
print(answer.choices[0].message.content)
```

Два прогона. Обычный: открой `05_retry.ipynb` в VS Code и нажми ▶ Run All — ответ с первой попытки. С искусственно малым таймаутом: поставь `TIMEOUT = 0.3` в той же ячейке и Run All снова — в выводе видны попытки с растущими паузами, потом либо успех, либо исключение после пятой. Третья проверка — разовая, конкретного факта, не обычный запуск лабы: временно поставь в `.env` `LLM_MODEL=nonexistent/model`, Restart Kernel и Run All — падает сразу, без ретраев: `NotFoundError` не входит в `RETRYABLE`, и это правильно. Верни `.env` и `TIMEOUT = 60.0` обратно.

## Шаг 8. results.md и коммит

Собери числа в `~/proj/ai-labs/day1-llm-basics/results.md`:

```markdown
# День 1 — измерения (дата, модель)

| Что | Значение |
|---|---|
| Токены EN / RU для сопоставимых фраз | … / … |
| temperature 0.0 — совпадений из 3 | … |
| Structured output — режим | json_schema / запасной |
| TTFT (медиана из 3) | … s через socks5 |
| Скорость генерации | … tok/s |
| Выход дороже входа | …x |
| 30k RAG-запросов/мес, основная модель | $… |
| 30k RAG-запросов/мес, дешёвая модель | $… |
| Ретраи при timeout=0.3 | … попыток до успеха / исключение |

Выводы в три строки: что удивило, что пойдёт в резюме, что проверить в день 5.
```

Перед публикацией из `~/proj/ai-labs`: `git add day1-llm-basics/*.py day1-llm-basics/results.md .gitignore`, затем `git diff --cached`. Проверь отсутствие ключей, приватного текста и URL с credentials; только после проверки коммит и push. Репозиторий портфолио публичный, .env и out не добавляй.

## Если не получилось

- **`403` от OpenRouter** — прокси не применился. Проверь `echo $HTTPS_PROXY`, что LXC 106 жив (`curl --proxy socks5h://192.168.0.106:1080 https://openrouter.ai/api/v1/models -o /dev/null -w '%{http_code}'`), и что стоит `httpx[socks]`, иначе создание SOCKS-транспорта завершается ошибкой отсутствующей зависимости.
- **`curl: (97) Can't complete SOCKS5 connection … (5)` или код `000`** — в `HTTPS_PROXY` стоит `socks5://` без `h`. Тогда curl резолвит `openrouter.ai` через локальный DNS, а резолвер провайдера отдаёт для этого имени другой адрес, до которого прокси в Казахстане не достучится. С `socks5h://` имя резолвит сам прокси. Python-скрипты дня этой ошибки не покажут: httpx всегда передаёт прокси имя хоста, поэтому расхождение видно только в curl.
- **`429` с `is temporarily rate-limited upstream` и `limit_source: upstream_provider_shared_pool`** — модель с суффиксом `:free` стоит в общей очереди всех пользователей OpenRouter, и провайдер её притормаживает независимо от твоего баланса. Ретрай тут почти бесполезен. Поставь в `LLM_MODEL` дешёвую платную модель с поддержкой `tools` и `structured_outputs` (проверь оба в `supported_parameters` ответа `/models`); на день 1 хватит центов. Бесплатные модели к тому же часто не умеют json_schema, а агент дня 4 отказывается считать их стоимость.
- **`content` пустой (`None`), `finish_reason: length` при маленьком `max_tokens`, а `usage` показывает десятки токенов** — модель рассуждает перед ответом (у DeepSeek V4 Flash и ряда других это включено по умолчанию). Скрытые токены рассуждений входят в `completion_tokens` и в счёт, в `completion_tokens_details.reasoning_tokens` видно сколько; провайдер может добавлять и скрытый системный промпт, поэтому `prompt_tokens` для одной и той же фразы отличается. Для лаб дня 1 возьми модель без рассуждений или отключи их: `extra_body={"reasoning": {"enabled": False}}` в `chat.completions.create` (расширение OpenRouter, не часть стандарта OpenAI).
- **`402 Payment Required`** — кончился баланс OpenRouter; пополни или переключись на бесплатную модель (в id есть `:free`), понимая, что у них лимиты и очередь.
- **`400` на `response_format`** — модель не поддерживает json_schema; скрипт сам уходит на запасной путь. Хочешь настоящий json_schema — смени модель.
- **`ValidationError`** в шаге 4 — модель вернула JSON не по схеме или обернула в текст. Посмотри `raw`, добавь в системный промпт «без markdown» (уже есть) или сделай второй запрос с текстом ошибки — это и есть ретрай с валидацией.
- **`usage` в стриме `None`** — провайдер или модель не отдают usage в стриме; посчитай tok/s по длине текста и оценке четыре символа на токен, пометив в отчёте как оценку.
- **Медленно всё** — socks5 через Казахстан добавляет сотни миллисекунд. Замерь TTFT без прокси там, где OpenRouter доступен напрямую, если есть такая возможность, и запиши обе цифры.

## Практика

Расширения на выбор, если осталось время:

1. Прогони `01_basics.ipynb` и `03_streaming.ipynb` против локальной Ollama из книги 23 (`OPENROUTER_BASE_URL=http://localhost:11434/v1`, `OPENROUTER_API_KEY=ollama`, `LLM_MODEL=<имя модели в Ollama>`): тот же код, нулевая цена за токен, другое качество и другая скорость — впиши в отчёт.
2. Проверь prompt caching: сделай системный промпт длиной больше двух тысяч токенов (вставь кусок документации), отправь два одинаковых запроса подряд и сравни поля usage, связанные с кэшем (у разных провайдеров называются по-разному; напечатай `r.usage` целиком).
3. Добавь в `02_structured.ipynb` автоматический ретрай при `ValidationError`: второй запрос с сообщением роли `user` вида «ошибка валидации: …, исправь JSON».

## Что проверить

- `career/vacancies-2026-09.md` содержит 20 строк и подсчёт требований; три полных текста лежат в `~/proj/ai-labs/data/vacancies/`.
- В `~/proj/ai-labs/day1-llm-basics/` семь файлов: `client.py`, пять ноутбуков `01`–`05`, плюс `results.md`; репозиторий закоммичен и запушен.
- `02_structured.ipynb` вернул валидные объекты для всех трёх вакансий; в отчёте указан режим.
- `results.md` содержит числа: токены RU/EN, TTFT, tok/s, коэффициент выход/вход, две месячные стоимости.
- `05_retry.ipynb` с `TIMEOUT = 0.3` показал растущие паузы, а несуществующая модель упала без ретраев.
- В отчёте есть три строки выводов, и одна из них — про то, что пойдёт в резюме.
