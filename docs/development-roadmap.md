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
- [x] Real-time color-coded ANSI tree progress reporting (`\033[1;32m` done, `\033[1;33m` in-progress, `\033[0;90m` pending, `\033[1;31m` blocked) in tool outputs and harness directives.
- [x] GitHub Releases/Tags update checker service with local caching and CLI/TUI integration.


## Phase 3: Transparent Local Proxy & Zero-Restart Auto-Rotation (Completed - v1.2.0)
- [x] Local Root CA & SSL Certificate Generator (`cert_service.py`) with SubjectAltName for `*.googleapis.com`.
- [x] Asyncio TCP/TLS MITM Proxy Server (`proxy/server.py`) handling HTTP `CONNECT` tunnels and TLS termination.
- [x] Dynamic Token Swapper & 429 Interceptor (`proxy/interceptor.py`): swaps Bearer tokens on the fly and auto-rotates + retries on HTTP 429 quota exhaustion.
- [x] Background Daemon Process Control (`proxy/daemon.py`, `commands/proxy_cmd.py`).
- [x] Auto-Rotation Proxy & Zero-Manual-Config Shell Integration (`auto_config.py`, `shell_cmd.py`, `agent_cmd.py` with automatic `~/.zshrc` hook and revert).
- [x] Stream Framing & Chunked Transfer Decoder (`stream_utils.py`) resolving EOF on Keep-Alive Google Cloud Code Assist connections.
- [x] Interactive TUI Proxy Screen & Live Badge (`proxy_flows.py`, `interactive_renderer.py`, `interactive_tui.py`).
- [x] Dynamic Multi-Theme Engine (`theme_catalog.py`, `theme_manager.py`, `theme_flows.py`, `theme_model.py`) with 7 presets (Gruvbox Warm default, Emerald Forest, Cyber Dark, Dracula, Monokai Pro, Nord Arctic, Modern Minimal).
- [x] True-Green Quota Progress Bar Grading (`theme.py`, `tables.py`) with 24-bit TrueColor hex color coding (`#16a34a` / `#22c55e`), eliminating terminal ANSI 32 cyan/teal mangling.
- [x] Interactive Theme Selector Screen (`[*] Color Themes`) in TUI with live progress bar preview and instant persistence in `~/.config/betteragy/accounts.json`.
- [x] First-Run Onboarding Flow & Auto-Setup Wizard (`onboarding_service.py`, `onboarding_wizard.py`) with 5-step guided setup (Keychain discovery, reasoning harness, MCP server, shell alias, system diagnostics).


## Phase 4: IDE Realtime Integration (Planned - v0.3.0 / v1.3.0)
- [ ] Direct Language Server process detector via process argv scanning (`--https_server_port`, `--csrf_token`).
- [ ] Programmatic `RegisterGdmUser` trigger when Antigravity IDE is open for zero-reload IDE switching.
- [ ] Context window token breakdown (MCP tools, system prompts, skills, workflows).

## Phase 5: Team & Extended Telemetry (Planned - v0.4.0)
- [ ] Multi-user / team shared pool synchronization.
- [ ] Export reports to Markdown, CSV, and HTML.
- [ ] Notification hooks (macOS notifications / desktop alerts when quota resets or reaches 0%).


