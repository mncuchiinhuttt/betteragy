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

## Phase 2: IDE Realtime Integration (Planned - v0.2.0)
- [ ] Direct Language Server process detector via process argv scanning (`--https_server_port`, `--csrf_token`).
- [ ] Programmatic `RegisterGdmUser` trigger when Antigravity IDE is open for zero-reload IDE switching.
- [ ] Context window token breakdown (MCP tools, system prompts, skills, workflows).

## Phase 3: Team & Extended Telemetry (Planned - v0.3.0)
- [ ] Multi-user / team shared pool synchronization.
- [ ] Export reports to Markdown, CSV, and HTML.
- [ ] Notification hooks (macOS notifications / desktop alerts when quota resets or reaches 0%).
