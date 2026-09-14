# Phase 3: Built-in Betteragy To-Do MCP Server Engine

## Context Links
- Master Plan: [plan.md](file:///Users/vominhlong/betteragy/plans/260914-2140-agy-deep-thinking-and-todo-harness/plan.md)
- Phase 2 Spec: [phase-02-deep-thinking-harness-and-rules.md](file:///Users/vominhlong/betteragy/plans/260914-2140-agy-deep-thinking-and-todo-harness/phase-02-deep-thinking-harness-and-rules.md)

## Overview
- **Priority**: High
- **Current Status**: Pending
- **Brief Description**: Implement a lightweight, zero-dependency Model Context Protocol (MCP) server inside `betteragy` that exposes native To-Do list tools (`todo_init`, `todo_add`, `todo_update`, `todo_list`, `todo_clear`) to `agy`, persisted in a local SQLite database.

## Key Insights
- `agy` connects to MCP servers over standard `stdio` JSON-RPC 2.0 (as configured in `~/.gemini/settings.json` or `~/.gemini/config/mcp_config.json`).
- Python has standard `json` and `sys.stdin`/`sys.stdout` which allows a blazing fast, zero-external-dependency JSON-RPC stdio server running via `python3 -m betteragy.mcp.todo_server`.
- When registered, `agy` automatically discovers the `todo_*` tools and presents them to Gemini/Claude/GPT models as first-class callable functions.
- State is persisted in SQLite (`~/.config/betteragy/tasks.db`), enabling real-time cross-process sync with the Betteragy TUI and CLI.

## Requirements
### Functional Requirements
- Stdio JSON-RPC 2.0 server supporting MCP methods:
  - `initialize`
  - `tools/list`
  - `tools/call`
- MCP Tools:
  1. `todo_init(project_name, goal)`: Initialize a new execution session with goal.
  2. `todo_add(title, description, priority)`: Add an atomic task to the board.
  3. `todo_update(task_id, status, notes, verification_evidence)`: Update status (`pending`, `in_progress`, `completed`, `blocked`).
  4. `todo_list(status_filter)`: Return all tasks with current state.
  5. `todo_clear()`: Archive or reset tasks for current workspace.
- Seamless CLI command to register into `agy`: `betteragy mcp install-todo`.

### Non-Functional Requirements
- Keep server logic modular and strictly under 200 lines per file.
- SQLite WAL mode for fast non-blocking concurrent reads and writes.
- Sub-5ms response time per MCP tool call.

## Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                      Antigravity CLI (agy)                  │
│                     (Claude / Gemini / GPT)                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
                      stdio JSON-RPC 2.0
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             betteragy MCP To-Do Server                      │
│             (betteragy.mcp.todo_server)                     │
│                                                             │
│   ┌─────────────────────┐       ┌───────────────────────┐   │
│   │   JSON-RPC Dispatch │ <───> │   TaskService         │   │
│   └─────────────────────┘       └───────────┬───────────┘   │
└─────────────────────────────────────────────┼───────────────┘
                                              │
                                              ▼
                             ┌─────────────────────────────────┐
                             │ ~/.config/betteragy/tasks.db    │
                             │ (SQLite WAL Database)           │
                             └─────────────────────────────────┘
```

## Related Code Files
- Files to create:
  - `src/betteragy/mcp/__init__.py`
  - `src/betteragy/mcp/protocol.py`
  - `src/betteragy/mcp/task_db.py`
  - `src/betteragy/mcp/todo_tools.py`
  - `src/betteragy/mcp/todo_server.py`
  - `src/betteragy/mcp/mcp_registrar.py`
  - `src/betteragy/commands/mcp_cmd.py`
- Files to modify:
  - `src/betteragy/cli.py`

## Implementation Steps
1. Create `task_db.py` managing SQLite schema (`tasks` table: id, session_id, title, status, priority, evidence, timestamps).
2. Create `protocol.py` handling JSON-RPC 2.0 framing over stdin/stdout.
3. Implement MCP tool handlers in `todo_tools.py`.
4. Create entrypoint `todo_server.py`.
5. Build `mcp_registrar.py` to add `betteragy-todo` to `~/.gemini/settings.json`.

## Todo List
- [ ] Implement SQLite schema and CRUD operations in `task_db.py`
- [ ] Implement MCP stdio JSON-RPC transport in `protocol.py`
- [ ] Implement tool definitions and execution in `todo_tools.py`
- [ ] Implement MCP config injection in `mcp_registrar.py`
- [ ] Write unit tests for tool calls and SQLite persistence

## Success Criteria
- `agy mcp list` displays `betteragy-todo` as `enabled`.
- During an `agy` session, the model autonomously calls `todo_add` and `todo_update` when presented with a task.

## Risk Assessment
- **Risk**: Python virtual environment path differences.
- **Mitigation**: Registrar detects current Python executable path (`sys.executable`) to ensure exact virtualenv or system python resolution.

## Security Considerations
- Validate and sanitize all task string inputs to prevent SQL injection (use parameterized queries exclusively).

## Next Steps
- Implement Phase 4: Real-time ASCII Task Visualizer & TUI.
