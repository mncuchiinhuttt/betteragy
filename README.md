# Betteragy 🚀

A high-performance, aesthetically pleasing Rich Terminal CLI & TUI switchboard and token analytics engine for the Antigravity ecosystem (`agy` CLI and Antigravity IDE).

## Features
- **Instant Account Switching**: Proactively refreshes tokens and updates macOS Keychain / Linux Secret Service so `agy` instantly authenticates with zero reload.
- **Multi-Account Rotation**: Automatic rotation strategies (`round-robin`, `least-used`, `sticky`, `random`) with cooldown protection when rate-limited.
- **Live AI Quota & Reset Timers**: Directly queries Google Cloud Code Assist API for real-time model remaining percentages (Claude Opus, Sonnet, Gemini 3.1 Pro, Flash) and accurate countdowns.
- **Offline Token Analytics**: Directly parses local conversation SQLite databases (`~/.gemini/antigravity-cli/conversations/*.db`) with built-in protobuf decoder to calculate all-time tokens (Input, Output, Cache, Thinking) and estimated USD costs ($) with zero background server dependencies.
- **Rich TUI Dashboard**: Live auto-updating multi-panel terminal dashboard built with Python `rich`.

## Quick Start
```bash
# Install locally with uv
uv pip install -e .

# List accounts
betteragy account list

# View live AI quotas
betteragy quota

# View token usage and cost analytics
betteragy usage

# Launch live dashboard
betteragy dashboard
```
