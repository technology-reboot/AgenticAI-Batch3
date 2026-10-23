"""Steps 4-5: connect the Lab 1 MCP server to a LangChain/LangGraph ReAct
agent using MultiServerMCPClient + load_mcp_tools, then ask it the same
question as raw_tools_agent.py.

Run:
    python langchain_mcp_agent.py

This launches server.py itself as a stdio subprocess -- no separate "run the
server first" step is needed, and the same server.py also works unmodified
as a Claude Desktop MCP server (see claude_desktop_config.example.json).
"""

import asyncio
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

from llm import get_llm

SERVER_PATH = Path(__file__).parent / "server.py"
QUESTION = "What is the current P/E ratio of TCS?"


async def main() -> None:
    client = MultiServerMCPClient(
        {
            "financial-data": {
                "command": sys.executable,
                "args": [str(SERVER_PATH)],
                "transport": "stdio",
            }
        }
    )

    async with client.session("financial-data") as session:
        tools = await load_mcp_tools(session)
        print(f"Loaded {len(tools)} MCP tools: {[t.name for t in tools]}\n")

        agent = create_react_agent(get_llm(), tools)

        print(f"[MCP agent] Question: {QUESTION}\n")
        result = await agent.ainvoke({"messages": [("user", QUESTION)]})
        print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
