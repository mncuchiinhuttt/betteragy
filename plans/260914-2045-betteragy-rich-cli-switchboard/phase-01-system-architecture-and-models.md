# Phase 01: System Architecture, Environment & Core Models

## Overview
- **Priority**: P0 (Foundation)
- **Current Status**: Planned
- **Description**: Establish project structure, dependency packaging (`pyproject.toml` with `uv`), constants, configuration storage, and core domain data models.

## Key Insights
- Antigravity uses standard locations across macOS/Linux/Windows:
  - CLI: `~/.gemini/antigravity-cli/`
  - IDE: `~/.gemini/antigravity/`
  - Keyring service: `service="gemini"`, `account="antigravity"`.
- Configuration storage should follow XDG standards: `~/.config/betteragy/accounts.json` and `~/.config/betteragy/cache.json`.

## Architecture & Data Flow
```
pyproject.toml / uv
  └── src/betteragy/
        ├── core/
        │     ├── constants.py
        │     ├── config.py
        │     └── models.py
```

## Related Code Files
- [NEW] `pyproject.toml`
- [NEW] `src/betteragy/__init__.py`
- [NEW] `src/betteragy/core/constants.py`
- [NEW] `src/betteragy/core/config.py`
- [NEW] `src/betteragy/core/models.py`

## Implementation Steps
1. Setup `pyproject.toml` configuring entry point `betteragy = "betteragy.cli:app"` with dependencies: `rich`, `typer[all]`, `pydantic`.
2. Define `constants.py`: OAuth client credentials, endpoints (`loadCodeAssist`, `retrieveUserQuota`), model display maps, default paths.
3. Implement `models.py`: Pydantic models for `AccountRecord`, `StoredTokens`, `QuotaBucket`, `AccountQuota`, `TokenUsage`, `ConversationSummary`, `AggregatedUsage`.
4. Implement `config.py`: Cross-platform configuration reader and writer with safe atomic file writes and permission locking (`0o600`).

## Todo List
- [ ] Initialize project configuration (`pyproject.toml`)
- [ ] Implement core constants and paths
- [ ] Define data models
- [ ] Implement atomic config manager
- [ ] Verify environment setup via `uv pip install -e .`
