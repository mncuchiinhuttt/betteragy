# Betteragy Development Roadmap

## Phase 1: Core Switchboard & Analytics (Completed - v0.1.0)
- [x] Multi-account management and secure storage in `~/.config/betteragy/accounts.json`.
- [x] Platform keyring injection (`go-keyring-base64`) for macOS Keychain and Linux Secret Service.
- [x] Proactive OAuth token refresh & auto-import from Keychain / legacy configs.
- [x] Live AI quota monitoring & reset countdowns via Google Cloud Code Assist API.
- [x] Offline SQLite conversation scanner with built-in Protobuf wire decoder.
- [x] LiteLLM model pricing & estimated cost calculations.
- [x] Rich CLI UI (tables, progress bars, hero KPI cards, live dashboard).
- [x] Account rotation strategies (`round-robin`, `least-used`, `sticky`, `random`) and cooldowns.
- [x] Headless account connection via `--token` and browser OAuth loopback.

## Phase 2: Deep Thinking Harness & Multi-Session Planning Engine (Completed - v1.0.0 & v1.1.0)
- [x] System prompt injection & verification harness (`betteragy harness install --strict`).
- [x] Native stdio MCP To-Do server (`betteragy.mcp.todo_server`) registered in `~/.gemini/config/mcp_config.json`.
- [x] SQLite-backed atomic task state management (`~/.config/betteragy/tasks.db`).
- [x] Real-time ASCII task visualizer & watcher (`betteragy tasks --watch`).
- [x] Interactive agent launcher with automated `--effort high` flags (`betteragy agent`).
- [x] Multi-session concurrent process isolation across parallel `agy` terminal sessions (v1.1.0).
- [x] Process session affinity in MCP server and session filtering in CLI (`betteragy tasks sessions`, `betteragy tasks switch`).
- [x] Horizontal multi-tab session bar with Left/Right arrow & vi `h`/`l` interactive cycling.
- [x] Hierarchical single-width ASCII tree checklist output (`format_tasks_ascii_tree`) with status markers.
- [x] GitHub Releases/Tags update checker service with local caching and CLI/TUI integration.


## Phase 3: IDE Realtime Integration (Planned - v0.3.0)
- [ ] Direct Language Server process detector via process argv scanning (`--https_server_port`, `--csrf_token`).
- [ ] Programmatic `RegisterGdmUser` trigger when Antigravity IDE is open for zero-reload IDE switching.
- [ ] Context window token breakdown (MCP tools, system prompts, skills, workflows).

## Phase 4: Team & Extended Telemetry (Planned - v0.4.0)
- [ ] Multi-user / team shared pool synchronization.
- [ ] Export reports to Markdown, CSV, and HTML.
- [ ] Notification hooks (macOS notifications / desktop alerts when quota resets or reaches 0%).

