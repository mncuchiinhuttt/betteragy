# Betteragy Project Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-09-15

### Added
- **Transparent Local MITM Proxy & Auto-Rotation Subsystem**:
  - **Local Root CA & Server Certificate Generator (`cert_service.py`)**: Automatically creates and manages 2048-bit RSA Root CA (`ca.crt`, `ca.key`) and server certificate (`server.crt`, `server.key`) with SAN for `*.googleapis.com`, `cloudcode-pa.googleapis.com`, `daily-cloudcode-pa.googleapis.com`, and `127.0.0.1`.
  - **Universal CA Bundle (`ca_bundle.crt`)**: Combines local Root CA with macOS system certificates (`/etc/ssl/cert.pem`) into `ca_bundle.crt` to prevent Go `x509: certificate signed by unknown authority` errors on public endpoints (e.g., `lh3.googleusercontent.com`).
  - **Robust HTTP/1.1 Stream & Chunked Framing (`stream_utils.py`)**: Implements `stream_chunked_response`, `stream_fixed_response`, and `read_chunked_payload` to resolve EOF errors on keep-alive connections to `loadCodeAssist`.
  - **Dynamic Token Interceptor & Auto-Rotation (`proxy/interceptor.py`)**: Intercepts decrypted HTTP streams from `agy`, dynamically injects valid Bearer tokens from Betteragy's active account (`ensure_valid_access_token()`), intercepts HTTP 429 quota exhaustion errors, puts the exhausted account on a 4-hour cooldown, triggers automatic rotation (`RotationService.rotate()`), and transparently retries upstream with the new account's token so `agy` never encounters rate limits or errors.
  - **Zero-Manual-Export Shell Environment Auto-Config (`auto_config.py`, `daemon.py`)**: Automatically injects bounded shell functions `agy()` and `antigravity()` into `~/.zshrc` on proxy start, and cleanly reverts the configuration on stop. When stopped, shell functions immediately bypass proxy if `proxy.pid` is absent.
  - **Daemon Process Control (`proxy/daemon.py`, `commands/proxy_cmd.py`)**: Background process manager supporting `betteragy proxy start`, `stop`, `status`, and `run` with PID tracking, health probing, and logging.
  - **Auto-Rotation Proxy TUI Screen & Live Badge (`proxy_flows.py`, `interactive_renderer.py`, `interactive_tui.py`)**: Added `[*] Auto-Rotation Proxy` menu item, active proxy status badge in the header (`[ok] Active (45124)`), and dedicated control panel to toggle proxy daemon with `p`.
  - **Smooth Solid Block Progress Bar for AI Model Quotas (`theme.py`, `tables.py`, `test_quota.py`)**:
    - Upgraded progress bar to modern, seamless solid blocks `███████░░░░░░░  47%` with filled blocks (`█`), dimmed track shade (`░`), and right-aligned percentage.
    - Added responsive color threshold grading (green >= 50%, yellow >= 20%, red < 20%).
  - **Reasoning Harness Request Tiers & Proactive Clarification Gate (`strict_harness.md`, `balanced_harness.md`, `templates.py`)**:
    - Established 3 Request Complexity Tiers (Tier 1: Atomic 1-2 tasks max, Tier 2: Features 2-4 tasks, Tier 3: Architecture 4-6 tasks) to eliminate artificial planning bureaucracy for simple requests.
    - Added Mandatory Proactive Clarification Gate instructing the agent to pause and ask structured follow-up questions with recommended options whenever user intent, UI layout, or requirements have trade-offs.
  - **Dynamic Theme Engine & Color Palette Customization (`theme_catalog.py`, `theme_model.py`, `theme_manager.py`, `theme_flows.py`, `menu_dispatcher.py`)**:
    - Implemented 7 built-in theme presets: **Gruvbox Warm** (Default, optimized for warm ivory/cream terminal backgrounds with terracotta rust, forest green, and amber highlights), **Emerald Forest** (lush greens, mint & sage), **Cyber Dark** (neon cyan & magenta), **Dracula** (vibrant purple & pastel pink), **Monokai Pro** (sunny yellow & lime), **Nord Arctic** (frost blue & polar night), and **Modern Minimal** (clean monochrome).
    - Added TUI Theme Selector Screen (`[*] Color Themes`) accessible from Main Menu with live quota progress bar sample previews and instant theme switching.
    - Added `theme` persistence to `AccountsStorage` (`~/.config/betteragy/accounts.json`).
    - Modularized `menu_dispatcher.py` to keep all interactive TUI files strictly under 170 lines.
  - **True-Green Quota Progress Bar Grading (`theme.py`, `tables.py`, `test_quota.py`, `test_theme.py`)**:
    - Replaced ambiguous ANSI 32 color name with explicit 24-bit TrueColor hex codes (`#16a34a` / `#22c55e` / `#50fa7b` / `#a9dc76` / `#a3be8c`) across all themes, guaranteeing that high quota (>= 50%) is unequivocally vibrant green and never rendered as blue or teal regardless of the terminal emulator's custom ANSI 16 color map.
    - Dynamically themed status badges (`[*] Active`, `[+] Ready`, `[!] Cooldown`, `[x] Disabled`), table titles, headers, borders, cursors, and selection highlights.
  - **Comprehensive Unit & Integration Test Suite (`test_theme.py`, `test_cert_service.py`, `test_proxy.py`, `test_proxy_tui.py`, `test_auto_config.py`, `test_quota.py`, `test_interactive_tui.py`, `test_agent_cmd.py`)**: Full automated test coverage with 78/78 tests passing.
  - **Agent Tool Auto-Approval (`agent_cmd.py`, `test_agent_cmd.py`)**:
    - Added `--dangerously-skip-permissions` (`-y`, default enabled) to `betteragy agent` and `betteragy agent run`, auto-approving all tool permission requests without interrupting autonomous workflows.
    - Updated `betteragy agent setup-alias` to configure `alias agy="agy --effort high --dangerously-skip-permissions"`.
  - **OMP Battle-Tested Superpowers Synthesis (`strict_harness.md`, `balanced_harness.md`, `harness_service.py`)**:
    - Scanned Oh My Pi (`@oh-my-pi/pi-coding-agent`) architecture and integrated proven invariants:
      - **Inviolable Delivery Contract**: Never yield while actionable work remains in the turn; phase boundaries and to-do updates never pause execution; strictly zero mocks, stubs, or `TODO: implement` placeholders.
      - **User Ground-Truth Axiom**: User-reported observations, errors, and terminal logs are ground truth; never waste turns re-running checks to confirm what the user reported.
      - **Clean Cutover Rule**: When refactoring interfaces, update all callers across the codebase and purge obsolete code and deprecated shims.
      - **Anti-Spinning Loop Guards**: Detect and immediately break circular thinking/deliberation loops by picking the most boring viable choice and making a concrete tool call; prevent repetitive failing tool calls.
      - **Task Batching & Smoke Testing**: Prohibit isolated to-do calls (always batch with real edits/tests); conduct live behavioral smoke testing on CLIs and servers.
  - **Real-Time Color-Coded Progress & ANSI Tree Reporting (`todo_tools.py`, `strict_harness.md`, `balanced_harness.md`, `harness_service.py`, `test_todo_formatting.py`)**:
    - **Step-by-Step Live Output**: MCP tools `todo_add` and `todo_update` automatically format and return the full updated TODO tree directly in tool outputs, enabling immediate visibility at every step.
    - **Color-Coded ANSI Tree Output**: Added standard ANSI escape codes to `format_tasks_ascii_tree` with vibrant green for completed `[x]`, warm yellow/amber for active `[>]`, dim gray for pending `[ ]`, bold red for blocked `[!]`, and cyan/white for headers and progress ratios (`done/total`).
    - **Harness Enforcement**: Formulated mandatory harness directives requiring the agent to output the color-coded to-do tree in an ````ansi code block at every progress transition (`in_progress`, `completed`), eliminating end-of-session dump delays.
    - **Robust Regex Replacement**: Fixed `re.sub` escaping in `harness_service.py` to handle backslashes in replacement content without raising `re.error: bad escape`.


## [1.1.0] - 2026-09-14

### Added
- **Multi-Session Task Planning & Process Isolation**:
  - **Concurrent Session Engine (`task_db.py`, `task_schema.py`)**: Enhanced SQLite schema with `sessions` table tracking `id`, `goal`, `project_name`, `working_dir`, `created_at`, `updated_at`, `is_active`. Fully supports concurrent `agy` processes running across different workspaces or terminal tabs without collisions.
  - **MCP Process Session Affinity (`todo_server.py`, `todo_tools.py`)**: `TodoServer` stdio process automatically binds `session_id` upon `todo_init` and maintains session affinity across all subsequent tool calls (`todo_add`, `todo_update`, `todo_list`, `todo_clear`).
  - **CLI Session Management Commands (`tasks_cmd.py`, `task_renderer.py`)**:
    - Added `betteragy tasks sessions` to list all planning sessions with goal, project, completion %, and task counts.
    - Added `betteragy tasks switch <id>` to switch active session focus.
    - Added `--session <id>` flag to `betteragy tasks`, `betteragy tasks watch`, `betteragy tasks clear`, and `betteragy tasks add`.
  - **Horizontal Multi-Tab Session Bar with Left/Right Navigation**:
    - Embedded dynamic horizontal session tabs (`render_session_tab_bar`) at the top of the Task Board showing session ID, project name, and verification completion %.
    - Interactive Left/Right arrow keys (`KEY_LEFT`, `KEY_RIGHT`, `h`, `l`) to cycle smoothly through session tabs in both the interactive TUI and `betteragy tasks watch` CLI mode.
    - Sliding window layout with `[< Left]` and `[Right >]` edge markers when sessions exceed visible width.
    - Pressing `Enter` on any tab promotes that session to the globally active session.
  - **Interactive TUI Session Browser & Switcher (`session_flows.py`, `session_panels.py`, `interactive_tui.py`)**:
    - Press `s` in `Tasks & Planning` screen to open the interactive session list modal.
    - Navigate sessions with Up/Down and press Enter to switch the active session.
  - **ASCII Tree Checklist Output (`todo_tools.py`, `strict_harness.md`)**:
    - Implemented `format_tasks_ascii_tree` producing single-width ASCII tree checklist format (`|--`, `'--`, `` `----- ``) with task status markers (`[x]` Completed, `[>]` In Progress, `[ ]` Pending, `[!]` Blocked) and completion ratios (`X/Y`).
    - Injected strict formatting requirements into global reasoning harness so `agy` outputs identical ASCII tree checklists in conversational responses.
  - **GitHub Update Checker Service (`update_service.py`, `cli.py`, `interactive_tui.py`)**:
    - Added `UpdateService` to check GitHub Releases and Tags API with 2.0s low-latency timeout and 4-hour local caching in `~/.config/betteragy/update_cache.json`.
    - Added `betteragy update` and `betteragy check-update` CLI commands with update panel and upgrade instructions.
    - Added `[?] Check for Updates` to interactive TUI menu with dynamic `[update: vX.X.X]` header badge.
  - **Decoupled Architecture & Strict File Size Guardrail**:
    - Created `task_schema.py` (40 lines), `session_panels.py` (153 lines), and `session_flows.py` (60 lines) ensuring all source files stay strictly `< 200 lines`.
  - **Comprehensive Test Coverage**:
    - Added multi-session isolation tests, session affinity tests, and tab cycling tests in `test_session_tabs.py` (49/49 tests passing in 0.34s).

## [1.0.0] - 2026-09-14

### Added
- **Official Version Management (`v1.0.0`)**:
  - Unified version metadata across `src/betteragy/__init__.py` and `pyproject.toml`.
  - Added CLI `--version` / `-V` flags and `betteragy version` command.
  - Rendered version badge `v1.0.0` in the interactive TUI menu header and live dashboard footer.
- **Deep Reasoning & Verification Harness (`betteragy harness`)**:
  - Automatically installs and manages a 5-phase strict reasoning and falsification protocol into `~/.gemini/config/rules/betteragy-harness.md`.
  - Automatically loaded by `agy` on startup as `<RULE[user_global]>`.
  - Enforces mandatory planning, exploration before editing, compile checking after edits, and evidence-backed task completion.
  - Profile switching (`strict` vs `balanced`) via `betteragy harness install --profile <strict|balanced>`.
- **Built-in To-Do MCP Server (`betteragy.mcp.todo_server`)**:
  - Native JSON-RPC 2.0 stdio MCP server registered into `~/.gemini/config/mcp_config.json` and `~/.gemini/settings.json`.
  - Gives `agy` native function calling tools: `todo_init`, `todo_add`, `todo_update`, `todo_list`, `todo_clear`.
  - Persisted in SQLite WAL mode (`~/.config/betteragy/tasks.db`) for concurrent multi-process access.
- **ASCII Task Planning Visualizer (`betteragy tasks`)**:
  - Live ASCII task board rendering (`[ ]` Pending, `[>]` In Progress, `[ok]` Completed, `[x]` Blocked) with progress bar and evidence notes.
  - Real-time terminal watcher (`betteragy tasks --watch`) refreshing live as `agy` executes tasks.
  - Integrated into TUI menu as `[*] Tasks & Planning` and `[^] Thinking Harness`.
- **Agent Launcher & Alias Helper (`betteragy agent`)**:
  - Launches `agy` with high reasoning effort (`--effort high`).
  - `betteragy agent setup-alias` to automatically configure `alias agy="agy --effort high"` in `~/.zshrc`.

### Fixed
- **Harness Injection into Global Rules (`GEMINI.md`)**:
  - Resolved issue where `agy` did not see the Betteragy Harness because rules were saved to `~/.gemini/config/rules/` instead of `~/.gemini/GEMINI.md`.
  - `HarnessService` now manages bounded injection blocks (`<!-- BETTERAGY_HARNESS_START -->` ... `<!-- BETTERAGY_HARNESS_END -->`) directly in `~/.gemini/GEMINI.md`, ensuring `agy` automatically loads the harness as `<RULE[user_global]>`.
  - Updated harness prompt instructions with explicit MCP invocation syntax: direct `todo_init(goal=...)` and `call_mcp_tool(ServerName='betteragy-todo', ToolName='todo_init', Arguments={'goal': '...'})`.
- **Token Telemetry Extraction (`protobuf_decoder.py`)**:
  - Fixed reasoning tokens extraction: read thinking tokens from protobuf field 10 (`f4[10]`) instead of static flags field 6 (`f4[6] = 24`).
  - Extracted visible response tokens from field 9 (`f4[9]`), preserving `total_output = f9 + f10 = f3`.
  - Solved double-billing issue by ensuring total output does not add reasoning tokens twice.
- **MCP Server Protocol Negotiation (`betteragy-todo`)**:
  - Fixed `error: invalid request` error when initialized by `agy` CLI's Go MCP client.
  - Implemented SEP-2575 `server/discover` RPC supporting protocol version `2026-07-28` and `supportedVersions`.
  - Dynamically echo requested `protocolVersion` (e.g. `2025-11-25`) during legacy `initialize` handshake fallback.
  - Correctly ignored notifications without `id` per JSON-RPC 2.0 specification, avoiding spurious null-id error packets.
  - Added empty handlers for `prompts/list`, `resources/list`, and `resources/templates/list`.

### Changed
- **Token Pricing Table to 2026 Market Rates (`pricing_service.py`)**:
  - Updated pricing table with current official rates per 1M tokens:
    - Gemini 3.8 / 3.7 Flash: Input $0.75, Output $3.75, Cache Read $0.075, Reasoning $3.75.
    - Gemini 3.1 Pro: Input $2.00, Output $12.00, Cache Read $0.50, Reasoning $12.00.
    - Gemini 2.5 Pro: Input $1.25, Output $10.00, Cache Read $0.3125, Reasoning $10.00.
    - Gemini 2.5 Flash: Input $0.15, Output $0.60, Cache Read $0.0375.
    - Gemini 2.0 Flash: Input $0.10, Output $0.40, Cache Read $0.025.
    - Gemini 1.5 Flash: Input $0.075, Output $0.30, Cache Read $0.01875.
    - Claude 3.7 / 3.5 Sonnet: Input $3.00, Output $15.00, Cache Read $0.30, Cache Write $3.75.
    - Claude 3.5 Haiku: Input $0.80, Output $4.00, Cache Read $0.08, Cache Write $1.00.

## [0.1.0] - 2026-09-14


### Added
- **Interactive Arrow-Key TUI**:
  - Full-screen interactive application like coding agents / lazygit.
  - Arrow key navigation (Up/Down or k/j), Enter to select, Esc/b to go back, q to exit.
  - Alternate terminal screen buffer (`\033[?1049h`) with clean terminal state restoration on exit.
  - Interactive account selector, live quota view with manual refresh (`r`), usage KPIs, and rotate/cooldown triggers.
  - In-TUI Account Management: Direct Google browser OAuth authentication with live background listener, headless token prompt, and interactive account deletion directly from the TUI without leaving to the shell.

### Changed
- **ASCII-First Terminal Interface**:
  - Replaced all Unicode emojis, bullets, checkmarks, stars, and multi-width symbols with clean standard ASCII markers (`[~]`, `[#]`, `[$]`, `[*]`, `[!]`, `[+]`, `[-]`, `[>]`, `[x]`, `[ok]`, `|`, `[####----]`).
  - Completely eliminates terminal font rendering glitches and double-width cell misalignment across different terminal emulators.

### Fixed
- **TUI Arrow Key Escape Sequence Parsing**:
  - Replaced `sys.stdin.read(1)` with unbuffered `os.read(self.fd, 32)` in `key_listener.py` to prevent Python's `TextIOWrapper` from buffering subsequent escape sequence bytes (`[` and `B`), which previously caused `select()` to time out and mistakenly trigger `KEY_ESC`.
  - Added support for both CSI (`\x1b[`) and SS3 (`\x1bO`) terminal sequences as well as Page Up/Down keys.
  - Updated `interactive_tui.py` so pressing `ESC` on the main menu clears temporary status messages rather than terminating the app, reserving `q` or the explicit "Exit" menu item for intentional exit.

- **Account Switchboard**:
  - Direct keyring credential injection (`go-keyring-base64` envelope) for `agy` CLI on macOS Keychain and Linux Secret Service.
  - Proactive OAuth token refresh to prevent 401 unauthenticated errors.
  - Multi-account rotation strategies: `round-robin`, `least-used`, `sticky`, and `random`.
  - Rate-limit cooldown management (`betteragy account cooldown <hours>`).
  - Google OAuth 2.0 loopback flow and headless direct token addition (`--token`).
  - Auto-import active credentials from macOS Keychain and legacy `~/.pi/agent/antigravity-accounts.json`.
- **Live AI Quota Engine**:
  - Direct integration with Google Cloud Code Assist API (`loadCodeAssist` & `retrieveUserQuota`).
  - Humanized model catalog with variant qualifiers (Claude Opus 4.6 Thinking, Sonnet, Gemini 3.1 Pro, Flash, GPT-OSS 120B).
  - Accurate local timezone countdown timers (`in 1h 45m`).
  - Multi-account quota comparison matrix (`betteragy quota --all`).
  - Live auto-refresh watch mode (`betteragy quota --watch`).
- **Offline Token Analytics**:
  - Zero-dependency local SQLite scanner reading `~/.gemini/antigravity-cli/conversations/*.db`.
  - Protobuf wire decoder extracting Input, Output, Cache, and Reasoning tokens directly from disk.
  - LiteLLM pricing engine calculating estimated USD costs ($).
  - Timeframe filters: `today`, `24h`, `7d`, `30d`, and `all-time`.
  - Model usage breakdown (`betteragy usage models`).
  - Incremental disk cache (`~/.config/betteragy/usage_cache.json`) enabling <30ms response times.
- **Rich Terminal UI & Live Dashboard**:
  - Clean `rich` styled tables with rounded borders and threshold-colored progress bars.
  - High-impact hero KPI cards for active account, total tokens, and estimated cost.
  - Live full-screen TUI dashboard (`betteragy dashboard`).
  - Shell integration generator (`betteragy shell`).
