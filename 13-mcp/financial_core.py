"""Core financial-data logic, independent of how it gets exposed (MCP tool,
LangChain @tool, plain function call, ...).

Both server.py (the MCP server) and raw_tools_agent.py (the pre-MCP, Session 3
style agent) import these functions. That split is what makes the Lab 1
comparison in step 6 meaningful: the *logic* never changes, only the wrapper
around it does.
"""

from __future__ import annotations

import os

import requests
import yfinance as yf

NEWSAPI_URL = "https://newsapi.org/v2/everything"

# Tickers typed without a suffix (e.g. "TCS", "INFY") are tried as-is first,
# then against the NSE (.NS) and BSE (.BO) suffixes so Indian tickers work
# without the caller having to know yfinance's suffix convention.
_SUFFIXES_TO_TRY = ["", ".NS", ".BO"]


def _resolve_ticker(symbol: str) -> tuple[str, dict]:
    """Find a yfinance ticker symbol (and its .info dict) that has live data."""
    symbol = symbol.strip().upper()
    candidates = [symbol] if "." in symbol else [f"{symbol}{suf}" for suf in _SUFFIXES_TO_TRY]

    last_resolved, last_info = candidates[0], {}
    for candidate in candidates:
        info = yf.Ticker(candidate).info
        if info.get("currentPrice") is not None or info.get("regularMarketPrice") is not None:
            return candidate, info
        last_resolved, last_info = candidate, info
    return last_resolved, last_info


def get_stock_price_impl(symbol: str) -> str:
    resolved, info = _resolve_ticker(symbol)
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    if price is None:
        return f"Could not find a current price for '{symbol}'. Check the ticker symbol."

    name = info.get("longName") or info.get("shortName") or symbol
    currency = info.get("currency", "")
    return (
        f"{name} ({resolved}): {price} {currency} "
        f"(previous close: {info.get('previousClose')}, "
        f"day range: {info.get('dayLow')}-{info.get('dayHigh')})"
    )


def get_fundamentals_impl(symbol: str) -> str:
    resolved, info = _resolve_ticker(symbol)
    if not info or info.get("trailingPE") is None and info.get("currentPrice") is None:
        return f"Could not find fundamentals for '{symbol}'. Check the ticker symbol."

    name = info.get("longName") or info.get("shortName") or symbol
    return (
        f"Fundamentals for {name} ({resolved}):\n"
        f"- Trailing P/E: {info.get('trailingPE')}\n"
        f"- Forward P/E: {info.get('forwardPE')}\n"
        f"- EPS (trailing): {info.get('trailingEps')}\n"
        f"- Market Cap: {info.get('marketCap')}\n"
        f"- 52-week range: {info.get('fiftyTwoWeekLow')} - {info.get('fiftyTwoWeekHigh')}"
    )


def get_news_headlines_impl(query: str, max_results: int = 5) -> str:
    api_key = os.environ.get("NEWSAPI_KEY")
    if not api_key:
        return (
            "NEWSAPI_KEY is not set. Get a free key at https://newsapi.org and "
            "add it to your .env file to enable news headlines."
        )

    max_results = max(1, min(max_results, 20))
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": max_results,
        "apiKey": api_key,
    }
    try:
        resp = requests.get(NEWSAPI_URL, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
    except requests.RequestException as exc:
        return f"Error fetching news: {exc}"

    if not articles:
        return f"No recent news found for '{query}'."

    lines = [f"Recent headlines for '{query}':"]
    for i, article in enumerate(articles, start=1):
        title = article.get("title", "No title")
        source = (article.get("source") or {}).get("name", "Unknown source")
        published = article.get("publishedAt", "")
        lines.append(f"{i}. {title} ({source}, {published})")
    return "\n".join(lines)
