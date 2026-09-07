# ~/proj/ai-labs/day4-agent/memory_backend.py
import json
import os
import re
import uuid
from pathlib import Path

LOCAL = Path(__file__).resolve().parent / ".local" / "memory.json"
SEED = [{"title": "Учебный Ollama", "content": "Ollama слушает 11434. Учебные данные не содержат секретов.", "project": "ai-labs", "type": "knowledge"}]


def remote(action: str, payload: dict):
    import httpx

    # Удалённый сервис — только явный opt-in; проект задаёт оператор, не модель.
    project = os.getenv("MEMORY_REMOTE_PROJECT")
    if not project or payload.get("project") != project:
        raise ValueError("MEMORY_REMOTE_PROJECT должен совпадать с проектом запроса")
    with httpx.Client(timeout=30) as client:
        response = client.post(os.environ["MEMORY_URL"].rstrip("/") + "/" + action, json=payload)
        response.raise_for_status()
        return response.json()


def search_memory(query: str, project: str = "ai-labs") -> str:
    if os.getenv("MEMORY_URL"):
        items = remote("search", {"query": query, "project": project, "limit": 5})["results"]
    else:
        saved = json.loads(LOCAL.read_text()) if LOCAL.exists() else []
        words = set(re.findall(r"\w+", query.lower()))
        items = [r for r in SEED + saved if r["project"] == project and words.intersection(re.findall(r"\w+", (r["title"] + " " + r["content"]).lower()))][:5]
    return "\n\n".join(f"{i['title']}\n{i['content'][:500]}" for i in items) or "ничего не найдено"


def store_memory(title: str, content: str, project: str = "ai-labs") -> str:
    if not title.strip() or not content.strip() or len(title) > 200 or len(content) > 2000:
        raise ValueError("Некорректный размер заметки")
    item = {"title": title, "content": content, "project": project, "type": "knowledge", "scope": "project"}
    if os.getenv("MEMORY_URL"):
        return f"сохранено, id={remote('store', item)['id']}"
    LOCAL.parent.mkdir(parents=True, exist_ok=True)
    items = json.loads(LOCAL.read_text()) if LOCAL.exists() else []
    # Для однопроцессной лабы. В проде нужны транзакции и ключ идемпотентности.
    item["id"] = uuid.uuid4().hex
    items.append(item)
    temp = LOCAL.with_suffix(".tmp")
    temp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(LOCAL)
    return f"сохранено локально, id={item['id']}"
