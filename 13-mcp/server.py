"""Lab 1 - MCP server exposing 3 financial-data tools.

Run it directly to test with Claude Desktop (stdio transport):
    python server.py

Or point langchain_mcp_agent.py / test_server.py at it to drive it from code.
"""

from mcp.server.fastmcp import FastMCP

from financial_core import (
    get_fundamentals_impl,
    get_news_headlines_impl,
    get_stock_price_impl,
)

mcp = FastMCP("financial-data")


@mcp.tool()
def get_stock_price(symbol: str) -> str:
    """Get the current/latest stock price for a ticker symbol.

    Args:
        symbol: Stock ticker, e.g. "AAPL", "MSFT", or "TCS". Indian tickers
            without an exchange suffix are resolved automatically by trying
            .NS (NSE) and .BO (BSE).
    """
    return get_stock_price_impl(symbol)


@mcp.tool()
def get_fundamentals(symbol: str) -> str:
    """Get key fundamentals for a stock: trailing/forward P/E, EPS, market cap,
    and 52-week price range.

    Args:
        symbol: Stock ticker, e.g. "AAPL", "MSFT", or "TCS".
    """
    return get_fundamentals_impl(symbol)


@mcp.tool()
def get_news_headlines(query: str, max_results: int = 5) -> str:
    """Get recent news headlines about a company or topic.

    Args:
        query: Company name or topic to search news for, e.g.
            "Tata Consultancy Services".
        max_results: Maximum number of headlines to return (1-20, default 5).
    """
    return get_news_headlines_impl(query, max_results)


if __name__ == "__main__":
    mcp.run(transport="stdio")
