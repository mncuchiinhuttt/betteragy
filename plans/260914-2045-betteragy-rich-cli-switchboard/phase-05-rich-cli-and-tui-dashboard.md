# Phase 05: Rich CLI Commands & Interactive TUI Live Dashboard

## Overview
- **Priority**: P0 (User Interface & Experience)
- **Current Status**: Planned
- **Description**: Build terminal user interface using `rich` and `typer`: formatted tables, colored progress bars, KPI summary cards, interactive menus, and live auto-updating dashboard mode.

## Key Insights
- CLI must look modern and clean:
  - Rounded box borders (`box.ROUNDED`).
  - Quota progress bars with color thresholds (Green ≥ 50%, Yellow 20-49%, Red < 20%).
  - Hero KPI metrics (Total Tokens, Est. Cost, Active Account, Available Quota).
  - Clean error messages and spinners for network requests.
  - `--json` flag on all queries for scripting and CI/CD piping.

## CLI Command Surface
```bash
betteragy account list                # List all accounts, tiers & active indicator
betteragy account switch <id|email>   # Switch active account
betteragy account add                 # Add account via Google OAuth
betteragy account rotate              # Rotate to next healthy account
betteragy account cooldown [hours]    # Mark active exhausted, rotate

betteragy quota                       # View quota of active account
betteragy quota --all                 # View quota of all accounts side-by-side
betteragy quota --watch               # Live updating quota dashboard

betteragy usage                       # Overall token & cost summary
betteragy usage models                # Per-model breakdown
betteragy usage timeline              # Daily/monthly history
betteragy usage convo                 # Top conversations ranked by cost

betteragy dashboard                   # Full interactive Rich TUI dashboard
```

## Related Code Files
- [NEW] `src/betteragy/ui/theme.py`
- [NEW] `src/betteragy/ui/tables.py`
- [NEW] `src/betteragy/ui/cards.py`
- [NEW] `src/betteragy/ui/dashboard.py`
- [NEW] `src/betteragy/cli.py`

## Implementation Steps
1. Create `theme.py`: Color palette, status emojis/badges, styling helpers.
2. Create `tables.py`: Quota table, Account table, Usage breakdown table, Top conversations table.
3. Create `cards.py`: Hero KPI panels (Total Tokens, Cost, Active Account).
4. Create `dashboard.py`: Live multi-panel TUI layout updated periodically with `rich.live.Live`.
5. Create `cli.py`: Typer commands linking CLI commands to services and UI renderers.

## Todo List
- [ ] Implement Rich Theme & Formatters
- [ ] Implement Quota & Account Tables
- [ ] Implement Usage & Breakdown Tables
- [ ] Implement Live Dashboard View
- [ ] Implement Typer CLI Commands
