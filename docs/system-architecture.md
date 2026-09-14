# Betteragy System Architecture

## Overview
Betteragy is a high-performance Rich Terminal CLI and TUI switchboard and token analytics companion for the Antigravity ecosystem (`agy` CLI and Antigravity IDE).

## Architecture Diagram
```
                             ┌──────────────────────┐
                             │    betteragy CLI     │
                             │   (Typer / Click)    │
                             └──────────┬───────────┘
                                        │
     ┌──────────────────┬───────────────┴───────────────┬──────────────────┐
     ▼                  ▼                               ▼                  ▼
┌───────────────┐ ┌───────────────┐             ┌───────────────┐  ┌───────────────┐
│ Account &     │ │ Live Quota    │             │ Token Usage & │  │ Rich TUI &    │
│ Switchboard   │ │ Engine        │             │ Analytics     │  │ Dashboard     │
└───────┬───────┘ └───────┬───────┘             └───────┬───────┘  └───────┬───────┘
        │                 │                             │                  │
        ▼                 ▼                             ▼                  ▼
 • Keychain/Secret • CloudCode API               • SQLite Scanner   • Live Watch UI
   Service           (retrieveUserQuota)           (conversations/    • Tables & Bars
 • OAuth Loopback  • Model Catalog                 *.db)            • Hero KPI Cards
 • Rotation &        & Humanizer                 • Protobuf Decoder • Theme & Styles
   Cooldown        • Reset Timers                • LiteLLM Pricing
```

## Subsystems

### 1. Account & Keyring Switchboard (`betteragy.services.keyring_adapter`, `account_service`, `rotation_service`)
- Injects credential envelope `go-keyring-base64:<JSON>` directly into macOS Keychain / Linux Secret Service (`service="gemini"`, `account="antigravity"`).
- Proactively refreshes OAuth access tokens before injection to prevent 401 errors in `agy`.
- Supports rotation strategies (`round-robin`, `least-used`, `sticky`, `random`) and rate-limit cooldown timers.

### 2. Live AI Quotas & Reset Countdown (`betteragy.services.quota_service`, `model_catalog`)
- Queries Google Cloud Code Assist endpoints (`loadCodeAssist` & `retrieveUserQuota`).
- Humanizes raw model IDs (`claude-opus-4-6-thinking`, `gemini-3.1-pro-high`, `gpt-oss-120b-medium`).
- Computes local timezone reset countdowns (`in 1h 45m`).

### 3. Offline Token Usage & Analytics (`betteragy.services.usage_scanner`, `protobuf_decoder`, `pricing_service`)
- Scans local SQLite databases in `~/.gemini/antigravity-cli/conversations/*.db` and `conversation_summaries.db`.
- Built-in zero-dependency Protobuf wire decoder extracting Input, Output, Cache, and Reasoning tokens.
- Calculates estimated USD costs via LiteLLM model catalog.
- Incremental mtime cache (`~/.config/betteragy/usage_cache.json`) for <30ms query latency.

### 4. Rich Terminal UI / TUI Live Dashboard (`betteragy.ui.*`)
- Built with Python `rich` with rounded borders, threshold-colored progress bars, and hero KPI panels.
- Live dashboard loop (`betteragy dashboard` or `betteragy quota --watch`).

### 5. Deep Thinking Harness & Native To-Do MCP Engine (`betteragy.harness.*`, `betteragy.mcp.*`)
- **System Prompt & Verification Harness**: Injects strict chain-of-thought, falsification tests, and verification gates directly into `~/.gemini/config/rules/betteragy-harness.md`.
- **Built-in To-Do MCP Server**: Zero-dependency stdio JSON-RPC 2.0 server registered in `~/.gemini/settings.json`, providing `todo_init`, `todo_add`, `todo_update`, and `todo_list` tools backed by SQLite WAL (`~/.config/betteragy/tasks.db`).
- **Interactive ASCII Task Visualizer & Agent Launcher**: Real-time progress board (`betteragy tasks --watch` and `betteragy agent`) rendering atomic tasks as `[ ]`, `[>]`, `[ok]`, `[x]`.

