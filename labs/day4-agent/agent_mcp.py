# ~/proj/ai-labs/day4-agent/agent_mcp.py
import asyncio
import os
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from agent import build_graph, pricing, run
from tools import search_docs


async def main(question: str):
    client = MultiServerMCPClient({"memory": {
        "command": sys.executable,
        "args": [str(Path(__file__).resolve().with_name("mcp_memory_server.py"))],
        "transport": "stdio",
        # Выделенный клиент знает write-policy до получения инструментов.
        "env": {**os.environ, "MCP_MEMORY_WRITES": "1"},
    }})
    tools = await client.get_tools()
    print("MCP tools:", [t.name for t in tools])
    graph = build_graph([search_docs, *tools], await pricing())
    await run(graph, question, thread_id="mcp")


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "Найди в памяти заметку про Ollama в проекте ai-labs"))
