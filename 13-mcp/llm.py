"""Shared LLM factory so both agent scripts (raw-tools and MCP) use the same
model, picked via env vars so the lab works with either provider.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def get_llm(temperature: float = 0):
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), temperature=temperature)

    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
        temperature=temperature,
    )
