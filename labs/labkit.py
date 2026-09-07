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
