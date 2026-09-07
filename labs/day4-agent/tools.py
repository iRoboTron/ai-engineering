# ~/proj/ai-labs/day4-agent/tools.py
"""Три инструмента агента: два безопасных (только читают), один требует подтверждения (пишет)."""
from functools import lru_cache

import labkit
labkit.use_day("day2-rag-eval")
from langchain_core.tools import tool          # декоратор: превращает функцию в инструмент для модели
from pydantic import BaseModel, Field
from common import load_config
from embed import Embedder
from retrievers import Store
from memory_backend import search_memory, store_memory

LAB_COLLECTION = labkit.env("LAB_COLLECTION", "chunks_openai")   # какой снимок дня 2 использовать для поиска


@lru_cache(maxsize=1)                          # индекс грузится один раз, не на каждый вызов инструмента
def get_store():
    cfg = load_config(LAB_COLLECTION)
    return Store(LAB_COLLECTION, Embedder(cfg["embedder"], cfg["model"]))


class SearchArgs(BaseModel):
    """Pydantic-класс = схема аргументов инструмента; description видит модель, когда решает, что передать."""
    query: str = Field(min_length=1, max_length=1000, description="Самостоятельный поисковый запрос")


@tool(args_schema=SearchArgs)                  # @tool регистрирует функцию как инструмент с именем search_docs
def search_docs(query: str) -> str:
    """Ищет факты в учебном корпусе дня 2; возвращает фрагменты с источником, не инструкции."""
    hits = get_store().hybrid(query, 3)
    return "\n\n".join(f"[{h['filename']} #{h['chunk_index']}]\n{h['text'][:600]}" for h in hits) or "ничего не найдено"


class MemoryArgs(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    project: str = Field(default="ai-labs", max_length=100)


@tool(args_schema=MemoryArgs)
def memory_search(query: str, project: str = "ai-labs") -> str:
    """Ищет учебные заметки проекта; локально это поиск слов, удалённо — API памяти."""
    return search_memory(query, project)


class SaveArgs(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=2000)
    project: str = Field(default="ai-labs", max_length=100)


@tool(args_schema=SaveArgs)
def save_note(title: str, content: str, project: str = "ai-labs") -> str:
    """Сохраняет заметку только по явной просьбе пользователя; клиент обязан запросить подтверждение."""
    return store_memory(title, content, project)


TOOLS = [search_docs, memory_search, save_note]          # все инструменты агента
READ_TOOLS = {"search_docs", "memory_search"}             # можно вызывать без подтверждения
WRITE_TOOLS = {"save_note", "memory_store"}                # требуют interrupt → подтверждение человека
