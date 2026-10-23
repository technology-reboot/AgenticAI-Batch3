# Lab 1 · Build and connect an MCP server

**Objective:** Create an MCP server that exposes financial data tools, test it in Claude Desktop, then connect it to your LangChain agent from Session 3.

Everything in this lab has been installed and run end-to-end against live `yfinance` data (see [Expected output](#expected-output) below for a real run).

## Files

| File | Purpose |
|---|---|
| `financial_core.py` | Plain Python functions with the actual logic (yfinance + NewsAPI). Shared by both the MCP server and the raw-tools agent. |
| `server.py` | The MCP server (step 2). Wraps `financial_core` as 3 MCP tools: `get_stock_price`, `get_fundamentals`, `get_news_headlines`. |
| `test_server.py` | Standalone sanity check for the server (step 3) that doesn't require Claude Desktop. |
| `claude_desktop_config.example.json` | Config snippet to register the server in Claude Desktop (step 3). |
| `llm.py` | Picks Anthropic or OpenAI as the LLM for the agent scripts, via `.env`. |
| `raw_tools_agent.py` | The "Session 3" baseline: same 3 tools, but as in-process `@tool` functions, no MCP. |
| `langchain_mcp_agent.py` | Steps 4-5: connects to `server.py` via `MultiServerMCPClient` + `load_mcp_tools`, builds a ReAct agent, asks the P/E question. |
| `compare.py` | Step 6: runs both agents on the same question back-to-back. |

## Prerequisites

- Python 3.11+ (tested with 3.12)
- A free [NewsAPI](https://newsapi.org) key (optional — `get_news_headlines` degrades gracefully without one)
- An Anthropic or OpenAI API key for the LangChain agent scripts
- [Claude Desktop](https://claude.ai/download) for step 3

## Setup

```powershell
cd D:\Agentic-Batch2\13-mcp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# edit .env: add NEWSAPI_KEY, ANTHROPIC_API_KEY (or LLM_PROVIDER=openai + OPENAI_API_KEY)
```

## Step 1 — Install

```powershell
pip install mcp langchain-mcp-adapters
```

(`requirements.txt` installs this plus `langgraph`, `yfinance`, `requests`, the LLM provider packages, and `python-dotenv`.)

## Step 2 — The MCP server (`server.py`)

Built with `FastMCP` from the `mcp` package. It registers 3 tools, each a thin wrapper around `financial_core.py`:

- **`get_stock_price(symbol)`** — latest price, previous close, day range.
- **`get_fundamentals(symbol)`** — trailing/forward P/E, EPS, market cap, 52-week range.
- **`get_news_headlines(query, max_results=5)`** — recent headlines via NewsAPI.

Ticker resolution is automatic: a symbol without a `.` suffix (e.g. `"TCS"`) is tried as-is, then against `.NS` (NSE) and `.BO` (BSE), so Indian tickers work without the caller knowing yfinance's suffix convention.

## Step 3 — Test locally

**Option A — standalone (no Claude Desktop needed):**

```powershell
python test_server.py
```

This drives `server.py` over stdio exactly like an MCP host would: lists the 3 registered tools, then calls each one.

**Option B — Claude Desktop:**

1. Open `claude_desktop_config.example.json`, adjust the path to your checkout, and merge it into:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
2. Restart Claude Desktop.
3. Go to **Settings → Developer → MCP Servers** (or the tools icon in a chat) and confirm `financial-data` is listed with its 3 tools.
4. Ask Claude Desktop something like "What's TCS trading at?" and watch it call `get_stock_price`.

> Take your screenshot here for the lab deliverable.

## Step 4 — Connect to LangChain

`langchain_mcp_agent.py` launches `server.py` as a managed subprocess and loads its tools:

```python
client = MultiServerMCPClient({
    "financial-data": {
        "command": sys.executable,
        "args": [str(SERVER_PATH)],
        "transport": "stdio",
    }
})

async with client.session("financial-data") as session:
    tools = await load_mcp_tools(session)
```

## Step 5 — ReAct agent

```powershell
python langchain_mcp_agent.py
```

Builds a ReAct agent (`langgraph.prebuilt.create_react_agent`) over the 3 MCP tools and asks:

> What is the current P/E ratio of TCS?

The agent calls `get_fundamentals("TCS")` and answers using the `trailingPE` value the tool returns.

> **Note:** `create_react_agent` from `langgraph.prebuilt` prints a harmless deprecation warning on newer `langgraph` versions pointing at `langchain.agents.create_agent`. It still works correctly; this lab keeps the `langgraph.prebuilt` import since that's what `langchain-mcp-adapters`' own examples use today.

## Step 6 — Compare

```powershell
python compare.py
```

Runs the identical question through `raw_tools_agent.py`'s tools and the MCP-served tools, one after another, and prints a short diff of what changed in the *agent* code.

**What changed when switching from raw tools to MCP tools:**

- The tool *implementations* didn't change at all — both wrap the same `financial_core.py` functions.
- `raw_tools_agent.py` wraps them with `@tool` and hands them to `create_react_agent` directly, in-process.
- `langchain_mcp_agent.py` instead discovers them at runtime from an external process via `MultiServerMCPClient` + `load_mcp_tools(session)`. The agent-building code (`create_react_agent(llm, tools)` → `agent.ainvoke(...)`) is identical either way.
- The payoff: `server.py` is now also a fully working Claude Desktop tool server (step 3) with zero extra code — the same tools are reusable across any MCP host, not just this one LangChain script.

## Expected output

Real run of `test_server.py` (step 3, no API key needed for this part):

```
Registered tools (3):
  - get_stock_price: Get the current/latest stock price for a ticker symbol.
  - get_fundamentals: Get key fundamentals for a stock: trailing/forward P/E, EPS, market cap,
  - get_news_headlines: Get recent news headlines about a company or topic.

Calling get_stock_price(symbol='TCS') ...
Tata Consultancy Services Limited (TCS.NS): 2558.6 INR (previous close: 2506.9, day range: 2557.5-2625.0)

Calling get_fundamentals(symbol='TCS') ...
Fundamentals for Tata Consultancy Services Limited (TCS.NS):
- Trailing P/E: 17.78
- Forward P/E: 15.88
- EPS (trailing): 143.92
- Market Cap: 9257238921216
- 52-week range: 1976.8 - 3350.0

Calling get_news_headlines(query='Tata Consultancy Services') ...
NEWSAPI_KEY is not set. Get a free key at https://newsapi.org and add it to your .env file to enable news headlines.
```

(Numbers are live market data and will differ when you run it. With `NEWSAPI_KEY` set, the last call returns real headlines instead of the setup message.)

With a real `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env`, `python langchain_mcp_agent.py` answers the P/E question in natural language, e.g. *"TCS's current trailing P/E ratio is approximately 17.78."* — sourced from the `get_fundamentals` MCP tool call above.
