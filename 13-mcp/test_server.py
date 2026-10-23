"""Step 3 sanity check: talk to server.py over stdio exactly like an MCP
host would, without needing Claude Desktop installed. Confirms the 3 tools
register correctly and actually return data.

Run:
    python test_server.py
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = Path(__file__).parent / "server.py"


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER_PATH)])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = (await session.list_tools()).tools
            print(f"Registered tools ({len(tools)}):")
            for t in tools:
                print(f"  - {t.name}: {t.description.splitlines()[0]}")

            print("\nCalling get_stock_price(symbol='TCS') ...")
            result = await session.call_tool("get_stock_price", {"symbol": "TCS"})
            print(result.content[0].text)

            print("\nCalling get_fundamentals(symbol='TCS') ...")
            result = await session.call_tool("get_fundamentals", {"symbol": "TCS"})
            print(result.content[0].text)

            print("\nCalling get_news_headlines(query='Tata Consultancy Services') ...")
            result = await session.call_tool(
                "get_news_headlines", {"query": "Tata Consultancy Services", "max_results": 3}
            )
            print(result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
