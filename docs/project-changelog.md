# Betteragy Project Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-14

### Added
- **Interactive Arrow-Key TUI**:
  - Full-screen interactive application like coding agents / lazygit.
  - Arrow key navigation (`↑`/`↓` or `k`/`j`), `Enter` to select, `Esc`/`b` to go back, `q` to exit.
  - Alternate terminal screen buffer (`\033[?1049h`) with clean terminal state restoration on exit.
  - Interactive account selector, live quota view with manual refresh (`r`), usage KPIs, and rotate/cooldown triggers.

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
