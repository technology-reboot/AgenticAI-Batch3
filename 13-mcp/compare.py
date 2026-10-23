"""Step 6: run the SAME question through the raw-tools agent and the MCP
agent back to back, so the only variable is where the tools come from.

Run:
    python compare.py
"""

import asyncio

from langgraph.prebuilt import create_react_agent

import raw_tools_agent
from langchain_mcp_agent import QUESTION, SERVER_PATH
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from llm import get_llm
import sys


async def run_raw() -> str:
    tools = [
        raw_tools_agent.get_stock_price,
        raw_tools_agent.get_fundamentals,
        raw_tools_agent.get_news_headlines,
    ]
    agent = create_react_agent(get_llm(), tools)
    result = await agent.ainvoke({"messages": [("user", QUESTION)]})
    return result["messages"][-1].content


async def run_mcp() -> str:
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
        agent = create_react_agent(get_llm(), tools)
        result = await agent.ainvoke({"messages": [("user", QUESTION)]})
        return result["messages"][-1].content


async def main() -> None:
    print(f"Question: {QUESTION}\n")

    raw_answer = await run_raw()
    print("=== Raw Python @tool functions (Session 3 style) ===")
    print(raw_answer)

    mcp_answer = await run_mcp()
    print("\n=== Same tools served over MCP (Session 4 / Lab 1 style) ===")
    print(mcp_answer)

    print(
        "\n--- What changed in the agent code ---\n"
        "raw_tools_agent.py: tools are @tool-decorated Python functions living\n"
        "in the same process as the agent; create_react_agent(llm, tools) uses them directly.\n\n"
        "langchain_mcp_agent.py: tools are discovered at runtime from an external\n"
        "MCP server process via MultiServerMCPClient + load_mcp_tools(session); the\n"
        "agent code (create_react_agent + ainvoke) is otherwise identical. The tool\n"
        "implementation moved out-of-process and became reusable by any MCP host\n"
        "(e.g. Claude Desktop) without rewriting it as a LangChain tool each time."
    )


if __name__ == "__main__":
    asyncio.run(main())
