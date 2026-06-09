<p align="center">
  <img src="docs/assets/omclaw-banner.svg" alt="OmClaw" width="600"/>
</p>

<h1 align="center">OmClaw</h1>
<p align="center">
  <strong>A local-first autonomous AI coding agent — powered by Ollama.</strong><br/>
  Open-source · Self-hosted · Docker-sandboxed · Tool-calling · Git-aware
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue?style=flat-square&logo=python"/>
  <img src="https://img.shields.io/badge/FastAPI-async-green?style=flat-square&logo=fastapi"/>
  <img src="https://img.shields.io/badge/Ollama-local%20LLM-orange?style=flat-square"/>
  <img src="https://img.shields.io/badge/Docker-sandboxed-blue?style=flat-square&logo=docker"/>
  <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square"/>
</p>

---

## What is OmClaw?

OmClaw is an open-source, local-first autonomous coding agent similar in spirit to Claude Code, OpenDevin, and Codex CLI — but **100% self-hosted** using Ollama models. No cloud APIs, no data leaving your machine.

It lets you point an AI at a codebase and say *"build this feature"* or *"fix this bug"* — and it will plan, write code, execute it in a Docker sandbox, fix its own errors, commit results, and optionally open a GitHub PR.

---

## Key Features

| Feature | Status |
|---|---|
| Chat interface (terminal + web) | Phase 1 |
| Tool-calling architecture | Phase 1 |
| File read/write/list | Phase 1 |
| Docker sandbox execution | Phase 2 |
| Git operations (commit, branch, push) | Phase 3 |
| GitHub integration (repos, PRs) | Phase 4 |
| Project memory & goal tracking | Phase 5 |
| Semantic code search (FAISS/ChromaDB) | Phase 6 |
| Browser automation (Playwright) | Phase 7 |
| Self-healing coding loop | Phase 8 |

---

## Architecture Overview

```
User (CLI / Web UI)
        │
        ▼
┌─────────────────────────────────────────────┐
│              OmClaw Agent Controller         │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │  Planner │  │ Executor │  │  Memory   │ │
│  └──────────┘  └──────────┘  └───────────┘ │
└────────────────────┬────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │     Ollama (LLM)    │
          │   qwen2.5-coder:14b │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │     Tool Manager    │
          ├─────────────────────┤
          │ File Tools          │
          │ Terminal Tools      │
          │ Git Tools           │
          │ GitHub Tools        │
          │ Browser Tools       │
          │ Memory Tools        │
          │ Sandbox Tools       │
          └─────────────────────┘
                     │
          ┌──────────▼──────────┐
          │   Docker Sandbox    │
          │  (isolated exec)    │
          └─────────────────────┘
```

---

## Project Structure

```
omclaw/
├── backend/
│   ├── agent/            # AgentController, Planner, Executor loop
│   ├── llm/              # OllamaClient, tool schema builder
│   ├── tools/            # All tool implementations
│   │   ├── file_tools.py
│   │   ├── terminal_tools.py
│   │   ├── git_tools.py
│   │   ├── github_tools.py
│   │   ├── browser_tools.py
│   │   └── memory_tools.py
│   ├── memory/           # SQLite + FAISS memory layer
│   ├── sandbox/          # Docker sandbox manager
│   ├── git/              # GitPython wrapper
│   ├── github/           # PyGitHub wrapper
│   ├── browser/          # Playwright automation
│   ├── retrieval/        # Repo indexing, semantic search
│   ├── api/              # FastAPI routes
│   └── database/         # SQLAlchemy models, migrations
├── frontend/             # React 18 + TypeScript chat UI
├── tests/                # pytest test suite
├── docs/                 # Architecture docs, API reference
├── docker/               # Sandbox Dockerfile + compose
├── scripts/              # Dev setup, install helpers
├── .env.example
├── pyproject.toml
└── docker-compose.yml
```

---

## Quick Start

> **Prerequisites:** Python 3.12+, Docker, Ollama installed and running

```bash
# 1. Clone the repo
git clone https://github.com/Yad4o/Shawty.git omclaw
cd omclaw

# 2. Pull the model
ollama pull qwen2.5-coder:14b

# 3. Set up environment
cp .env.example .env
# Edit .env — set your GitHub PAT if you want GitHub tools

# 4. Install backend
cd backend
pip install -e ".[dev]"

# 5. Run
uvicorn api.main:app --reload
```

---

## Development Roadmap

| Phase | Scope | Status |
|---|---|---|
| **Phase 1** | Chat, tool calling, file tools | 🔲 Not started |
| **Phase 2** | Docker sandbox | 🔲 Not started |
| **Phase 3** | Git operations | 🔲 Not started |
| **Phase 4** | GitHub integration | 🔲 Not started |
| **Phase 5** | Memory & goal tracking | 🔲 Not started |
| **Phase 6** | Repo indexing + semantic search | 🔲 Not started |
| **Phase 7** | Browser automation | 🔲 Not started |
| **Phase 8** | Self-healing coding loop | 🔲 Not started |

Each phase is implemented one at a time. See [`docs/ROADMAP.md`](docs/ROADMAP.md) for detailed breakdown.

---

## Tech Stack

- **Runtime:** Python 3.12+, FastAPI, Pydantic v2
- **LLM:** Ollama (`qwen2.5-coder:14b` default)
- **Sandbox:** Docker SDK for Python
- **VCS:** GitPython, PyGitHub
- **Memory:** SQLite, FAISS / ChromaDB
- **Browser:** Playwright
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS

---

## License

MIT © [Om Yadao](https://github.com/Yad4o)
