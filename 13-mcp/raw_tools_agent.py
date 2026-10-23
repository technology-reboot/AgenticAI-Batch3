"""Step 6 baseline: a ReAct agent using the "Session 3" style of tools
raw Python functions wrapped with @tool, running in-process. No MCP involved.

Run:
    python raw_tools_agent.py
"""

import asyncio

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from financial_core import (
    get_fundamentals_impl,
    get_news_headlines_impl,
    get_stock_price_impl,
)
from llm import get_llm

QUESTION = "What is the current P/E ratio of TCS?"


@tool
def get_stock_price(symbol: str) -> str:
    """Get the current/latest stock price for a ticker symbol (e.g. AAPL, TCS)."""
    return get_stock_price_impl(symbol)


@tool
def get_fundamentals(symbol: str) -> str:
    """Get key fundamentals (P/E, EPS, market cap, 52-week range) for a ticker symbol."""
    return get_fundamentals_impl(symbol)


@tool
def get_news_headlines(query: str, max_results: int = 5) -> str:
    """Get recent news headlines about a company or topic."""
    return get_news_headlines_impl(query, max_results)


async def main() -> None:
    tools = [get_stock_price, get_fundamentals, get_news_headlines]
    agent = create_react_agent(get_llm(), tools)

    print(f"[raw-tools agent] Question: {QUESTION}\n")
    result = await agent.ainvoke({"messages": [("user", QUESTION)]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
