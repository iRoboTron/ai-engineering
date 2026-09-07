# ~/proj/ai-labs/day4-agent/agent_mcp.py
"""Тот же агент, что в agent.py, но инструмент памяти приходит по MCP, а не импортом Python-функции —
так же, как будет с настоящим внешним MCP-сервером."""
import asyncio
import os
import sys
from pathlib import Path

import labkit  # noqa: F401  подключает .env до запуска дочернего процесса
from langchain_mcp_adapters.client import MultiServerMCPClient
from agent import build_graph, pricing, run
from tools import search_docs

# --- НАСТРОЙКИ ---
QUESTION = "Найди в памяти заметку про Ollama в проекте ai-labs"


async def main(question: str):
    client = MultiServerMCPClient({"memory": {
        "command": sys.executable,                                              # тот же python, что и здесь
        "args": [str(Path(__file__).resolve().with_name("mcp_memory_server.py"))],
        "transport": "stdio",
        # Выделенный клиент знает write-policy до получения инструментов.
        "env": {**os.environ, "MCP_MEMORY_WRITES": "1"},
    }})
    tools = await client.get_tools()             # спрашивает у MCP-сервера список инструментов
    print("MCP tools:", [t.name for t in tools])
    graph = build_graph([search_docs, *tools], await pricing())
    await run(graph, question, thread_id="mcp")


if __name__ == "__main__":
    asyncio.run(main(QUESTION))
