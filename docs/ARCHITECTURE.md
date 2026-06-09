# OmClaw Architecture

## Overview

OmClaw follows a **Clean Architecture** pattern with clear separation between:
- **Agent Layer** — orchestration, planner, self-healing loop
- **LLM Layer** — Ollama client, tool schema builder
- **Tool Layer** — all executable capabilities
- **Infrastructure Layer** — database, sandbox, Git, GitHub, browser, memory

## Data Flow

```
User Message
     │
     ▼
FastAPI Route (/api/chat)
     │
     ▼
AgentController.run()
     │
     ├── Build context (history + system prompt + tool schemas)
     │
     ├── OllamaClient.chat()
     │         │
     │         ▼
     │    Ollama (local) → qwen2.5-coder:14b
     │         │
     │         ▼
     │    Response: text OR tool_calls
     │
     ├── If tool_calls:
     │     │
     │     ▼
     │   ToolRegistry.execute(tool_name, **args)
     │     │
     │     ├── FileTools  → read/write workspace files
     │     ├── SandboxTools → execute in Docker container
     │     ├── GitTools → commit, branch, push
     │     ├── GitHubTools → PR, repo, issue
     │     ├── BrowserTools → Playwright automation
     │     └── MemoryTools → FAISS retrieval
     │
     │   Inject tool results back into message history
     │   Loop back to OllamaClient.chat()
     │
     └── Final text response → save to DB → return to user
```

## Component Map

| Component | File | Phase | Responsibility |
|---|---|---|---|
| AgentController | `agent/controller.py` | 1 | Agentic loop orchestration |
| SelfHealingLoop | `agent/self_heal.py` | 8 | Error → fix → retry cycle |
| OllamaClient | `llm/client.py` | 1 | HTTP wrapper around Ollama API |
| ToolRegistry | `tools/registry.py` | 1 | Tool registration + dispatch |
| FileTools | `tools/file_tools.py` | 1 | Workspace file operations |
| SandboxManager | `sandbox/manager.py` | 2 | Docker container lifecycle |
| GitClient | `git/client.py` | 3 | GitPython wrapper |
| GitHubClient | `github/client.py` | 4 | PyGitHub wrapper |
| MemoryStore | `memory/store.py` | 5 | SQLite + FAISS hybrid memory |
| RepoIndexer | `retrieval/indexer.py` | 6 | Codebase semantic indexing |
| BrowserAutomation | `browser/automation.py` | 7 | Playwright web automation |

## Design Principles

### 1. Tool-First Architecture
Every agent action is expressed as a tool call. The LLM never writes to disk directly — it calls `write_file`. It never runs code directly — it calls `execute_command`. This keeps all side effects auditable and sandboxed.

### 2. Docker Sandbox Isolation
All code execution happens inside a Docker container. The agent cannot touch the host filesystem except through the mounted `/workspace` directory. Network access is disabled inside the sandbox by default.

### 3. Async-First
All I/O (LLM calls, file ops, DB queries, Docker exec, GitHub API) is async. The FastAPI server handles concurrent sessions without blocking.

### 4. Local-First
No external API calls required for core functionality. Ollama runs locally. The database is SQLite. Memory is FAISS on disk.

### 5. Extensibility
Adding a new tool: implement `BaseTool`, register in `ToolRegistry`. The schema is automatically exposed to the LLM. No other changes needed.

## Phase Implementation Status

```
Phase 1 — Chat + File Tools    ████████████ Complete (scaffolded)
Phase 2 — Docker Sandbox       ████████████ Complete (scaffolded)
Phase 3 — Git Operations       ████████████ Complete (scaffolded)
Phase 4 — GitHub Integration   ████████████ Complete (scaffolded)
Phase 5 — Memory System        ████████████ Complete (scaffolded)
Phase 6 — Repo Indexing        ████████████ Complete (scaffolded)
Phase 7 — Browser Automation   ████████████ Complete (scaffolded)
Phase 8 — Self-Healing Loop    ████████████ Complete (scaffolded)
```

All phases are scaffolded with production-quality code.
Each phase's tools need to be registered in `ToolRegistry` when enabling that phase.
