# Betteragy — Rich CLI Multi-Account Switchboard & Analytics Engine

Overview plan for building **Betteragy**, a high-performance, aesthetically crafted Rich CLI & TUI tool for Antigravity (`agy` and Antigravity IDE).

## Project Status: Planning

| Phase | Description | Status | Progress |
|---|---|---|---|
| [Phase 01](phase-01-system-architecture-and-models.md) | Project Setup, Config & Core Domain Models | Complete | 100% |
| [Phase 02](phase-02-account-and-switchboard-service.md) | Account Manager, OAuth Flow & Keyring Switchboard | Complete | 100% |
| [Phase 03](phase-03-quota-monitoring-engine.md) | Live AI Quotas, Tier Resolver & Reset Timers | Complete | 100% |
| [Phase 04](phase-04-usage-analytics-engine.md) | Offline SQLite & LS Usage Scanner & Cost Calculator | Complete | 100% |
| [Phase 05](phase-05-rich-cli-and-tui-dashboard.md) | Rich CLI Commands & Interactive TUI Live Dashboard | Complete | 100% |
| [Phase 06](phase-06-testing-and-verification.md) | Unit/Integration Tests & CLI Verification | Complete | 100% |

## Key Technical Decisions
- **Runtime**: Python 3.12+ with `typer` + `rich` (KISS, native SQLite, terminal UI excellence).
- **File Limits**: Strict adherence to < 200 lines per module with kebab-case naming.
- **Keyring Protocol**: Platform keyring injection (`go-keyring-base64`) compatible with `agy`.
- **Zero-Dependency Usage Scanner**: Offline SQLite parser for `conversations/*.db` + `conversation_summaries.db`.
