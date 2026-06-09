# OmClaw Development Roadmap

## Phase 1 — Foundation (Current)
**Goal:** Working agent that can chat and manipulate workspace files.

### Implementation Steps
1. `backend/core/config.py` — settings via pydantic-settings ✅
2. `backend/llm/client.py` — OllamaClient with tool calling ✅
3. `backend/tools/file_tools.py` — read/write/list/delete ✅
4. `backend/tools/registry.py` — tool dispatch ✅
5. `backend/agent/controller.py` — agentic loop ✅
6. `backend/api/main.py` — FastAPI app ✅
7. `backend/api/routes/chat.py` — chat endpoint ✅
8. `backend/database/models.py` — SQLAlchemy models ✅
9. Tests for all file tools ✅

### Acceptance Criteria
- [ ] `uvicorn backend.api.main:app` starts without errors
- [ ] `GET /api/health` returns Ollama status
- [ ] `POST /api/chat` returns agent response
- [ ] Agent uses `read_file`/`write_file` tools correctly
- [ ] All Phase 1 tests pass

---

## Phase 2 — Docker Sandbox
**Goal:** All command execution isolated in Docker.

### Implementation Steps
1. Build `docker/Dockerfile.sandbox`
2. Implement `SandboxManager` (already scaffolded)
3. Add `ExecuteCommandTool` wrapping `SandboxManager.execute()`
4. Register in `ToolRegistry`
5. Integration tests

### Acceptance Criteria
- [ ] `execute_command` tool runs code in container, not host
- [ ] Timeout enforced
- [ ] Memory limit enforced
- [ ] Output returned to agent

---

## Phase 3 — Git Operations
**Goal:** Agent can commit work, create branches, push.

### Implementation Steps
1. Wrap `GitClient` methods as tools
2. Add `GitStatusTool`, `GitCommitTool`, `GitBranchTool`, `GitPushTool`
3. Register in `ToolRegistry`

---

## Phase 4 — GitHub Integration
**Goal:** Agent can create repos and open PRs.

### Implementation Steps
1. Wrap `GitHubClient` methods as tools
2. Add `CreateRepTool`, `CreatePRTool`, `GetFileContentsTool`
3. Register in `ToolRegistry`

---

## Phase 5 — Memory System
**Goal:** Agent remembers facts, errors, and fixes across sessions.

### Implementation Steps
1. Wire `MemoryStore` into `AgentController`
2. Add `AddMemoryTool`, `SearchMemoryTool`
3. Auto-inject relevant memories into system prompt

---

## Phase 6 — Repository Indexing
**Goal:** Agent can semantically search a codebase.

### Implementation Steps
1. Wire `RepoIndexer` into session startup
2. Add `SearchCodeTool`
3. Agent uses search before writing code

---

## Phase 7 — Browser Automation
**Goal:** Agent can research and interact with web pages.

### Implementation Steps
1. Wrap `BrowserAutomation` methods as tools
2. Add `NavigateTool`, `GetPageContentTool`, `ClickTool`, `FillTool`
3. Register in `ToolRegistry`

---

## Phase 8 — Self-Healing Loop
**Goal:** Agent fixes its own code errors automatically.

### Implementation Steps
1. Wire `SelfHealingLoop` into agent response to code execution failures
2. Store (error, fix) pairs in `MemoryStore` for learning
3. Add configurable retry count
