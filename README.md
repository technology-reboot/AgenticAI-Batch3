# AgenticAI

Code for **Agentic AI Training** — a collection of hands-on Python modules covering structured outputs, retrieval-augmented generation (RAG), memory, tool use, guardrails, evaluation, and a capstone agentic application. This repository is used as the practical companion to the Agentic AI training delivered by **Technology Reboot**.

## Overview

The repo is organized as a sequence of training modules, each demonstrating a specific building block of agentic AI systems, from simple structured-output agents to multi-tool, memory-aware agents with guardrails and a full capstone use case.


## Prerequisites

- Python 3.10+
- An OpenAI API key (set as the `OPENAI_API_KEY` environment variable), used by the structured-output and several agentic modules
- For the RAG modules: a LangChain-compatible setup, and (for the local-model variants) a local LLM runtime

## Installation

```bash
git clone https://github.com/technology-reboot/AgenticAI.git
cd AgenticAI
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt   # if present; otherwise install per-module dependencies (see below)
```

Since each module is largely self-contained, install only what a given script needs, for example:

```bash
pip install openai pydantic
pip install langchain langchain-openai chromadb
```

## Usage

Set your API key:

```bash
export OPENAI_API_KEY="your-api-key-here"   # On Windows: set OPENAI_API_KEY=your-api-key-here
```

Run any module directly, for example:

```bash
python Module2.py
```

For the RAG modules, ensure the `ebooks/` folder is populated with source documents and `chroma_db/` is writable, then run:

```bash
python "Module 3 - RAG with Langchain.py"
```

For the capstone project:

```bash
python "Module 5 - Capstone Project.py"
```

## About

This repository accompanies the **Agentic AI Training** delivered by [Technology Reboot](https://github.com/technology-reboot), Shailesh Pardesi's independent AI consulting and training practice, covering practical, applied agentic AI development for enterprise audiences.

## License

No license has been specified for this repository. Please contact the repository owner before reusing this code outside of the training context.
