# Betteragy

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-88%2F88%20passing-success.svg)]()
[![Code Architecture](https://img.shields.io/badge/code%20architecture-YAGNI%20|%20KISS%20|%20DRY-informational.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An elite, high-performance Rich Terminal CLI/TUI switchboard, transparent auto-rotation MITM proxy, and autonomous agent orchestration suite for the Google Antigravity ecosystem (`agy` CLI and Antigravity IDE).

---

## Executive Overview

Antigravity developers face three persistent friction points in production workflows:
1. **Quota Exhaustion & Disruptive Restarts**: Hitting HTTP 429 rate limits mid-session halts autonomous coding and requires manually exporting credentials or restarting terminals.
2. **Context Amnesia on Long-Running Workflows**: Multi-day tasks lose memory across session restarts, lacking structured checkpoints and autonomous wake-up timers.
3. **Agent Blindness to Resource Quotas**: Autonomous agents have no visibility into token burn rates, model quotas, or account tiers to make proactive routing decisions.

**Betteragy** solves these problems with a unified, zero-dependency engineering architecture:
- A **Transparent MITM Auto-Rotation Proxy** that intercepts HTTP 429 quota exhaustion errors on the wire and swaps Bearer tokens on the fly without interrupting `agy`.
- An **11-Tool Native MCP Server** (`betteragy-todo`) equipping agents with deterministic task tracking, subagent delegation with dependency blockers, persistent multi-day checkpoints, and live quota intelligence.
- A **Deep Multi-Angle Reasoning Harness** enforcing 5-pillar analytical thinking, request complexity tiers, and real-time color-coded ANSI progress tracking.
- An **Interactive Rich TUI Switchboard** featuring 7 dynamic color themes (Gruvbox Warm default), 24-bit TrueColor quota grading, and horizontal multi-tab session navigation.

---

## System Architecture

```
                       +-------------------------------------------------------+
                       |              Developer / Antigravity CLI              |
                       |          (agy / Antigravity IDE Workspace)            |
                       +-------------------------------------------------------+
                                  |                               |
                   [HTTP / HTTPS Requests]           [Stdio JSON-RPC 2.0 (MCP)]
                                  |                               |
                                  v                               v
            +------------------------------------+  +------------------------------------+
            |   Betteragy Local MITM Proxy       |  |     Betteragy MCP Server Suite     |
            |         (127.0.0.1:8080)           |  |          (betteragy-todo)          |
            |                                    |  |                                    |
            |  - Dynamic Bearer Token Injection  |  |  * Task Planning: todo_init/add    |
            |  - Stream / Chunk Framing Parser   |  |  * Subagent Delegation: @role      |
            |  - 429 Quota Exhaustion Detection  |  |  * Dependency Engine: needs #id    |
            |  - 4-Hour Cooldown & Auto-Rotate   |  |  * Quota Intelligence: quota_status|
            |  - Zero-Restart Upstream Retry     |  |  * Memory Checkpoints: save/resume |
            +------------------------------------+  +------------------------------------+
                      |                  ^                   |                 ^
                      | (New Bearer)     | (Active Acc)      |                 |
                      v                  |                   v                 |
            +------------------------------------+  +------------------------------------+
            |      Account Management Pool       |  |       SQLite Storage Engine        |
            |  (Keychain / SecretService / JSON) |  |   (WAL Mode / Atomic Migrations)   |
            +------------------------------------+  +------------------------------------+
                                  |
                   [TLS Upstream with SAN CA Cert]
                                  |
                                  v
            +-------------------------------------------------------+
            |             Google Cloud Code Assist API              |
            |       (cloudcode-pa.googleapis.com / Gemini)          |
            +-------------------------------------------------------+
```

---

## Core Capabilities

### 1. Transparent Local Proxy & Zero-Restart Auto-Rotation
- **Zero Downtime on 429 Rate Limits**: Intercepts Google Cloud Code Assist API requests, injects valid OAuth access tokens from the active pool, and intercepts HTTP 429 quota exhaustion errors.
- **Instant Upstream Retry**: Transparently rotates to the next available account with fresh quota, puts the exhausted account on a 4-hour cooldown, and retries the upstream request on the same TCP connection. `agy` never sees a connection failure or rate limit.
- **Universal Root CA Generator**: Automatically generates 2048-bit RSA Root CA (`ca.crt`) and server certificates with SubjectAltName for Google Cloud Code Assist endpoints. Merges with system root certificates (`ca_bundle.crt`) to eliminate Go `x509: certificate signed by unknown authority` errors.
- **Zero-Manual-Export Shell Integration**: Injects bounded wrapper functions into `~/.zshrc` on proxy start and cleanly cleans them up on stop.

### 2. Native MCP Agent Control Suite (`betteragy-todo`)
Equips `agy` with an 11-tool JSON-RPC 2.0 stdio server discoverable via modern SEP-2575 `server/discover` and standard `initialize`:

| Tool Category | Tool Name | Description |
| :--- | :--- | :--- |
| **Task Planning** | `todo_init` | Initializes task session with goal, project name, and working directory. |
| | `todo_add` | Adds atomic subtask with priority, subagent assignment, and dependency constraints. |
| | `todo_update` | Updates status (`pending`, `in_progress`, `completed`, `blocked`) and logs verification evidence. |
| | `todo_list` | Generates real-time ASCII tree checklist with dependency badges and status markers. |
| | `todo_clear` | Clears all tasks in the current execution session. |
| **Quota Intelligence** | `quota_status` | Inspects live AI model percentages, entitlement tier, and reset countdowns with low-quota alerts. |
| | `account_list` | Lists all accounts in the pool, their active state, and entitlement tiers. |
| | `account_switch` | Switches the active account dynamically from tool calls to rotate quota before hitting rate limits. |
| **Persistent Memory** | `checkpoint_save` | Saves structured snapshot (accomplishments, next steps, context data) to SQLite. |
| | `checkpoint_resume`| Restores execution context from a named checkpoint across multiple sessions/days. |
| | `checkpoint_list` | Lists past checkpoints with timestamps and summaries. |

### 3. Subagent Delegation & Dependency Blocker Engine
- **Role Assignment**: Assign subtasks directly to specialized subagents using `todo_add(assigned_to="researcher")` rendered as `@researcher` in ASCII trees.
- **Prerequisite Enforcement**: Declare dependencies with `todo_add(depends_on="1,2")`. The tree formatter automatically detects unmet dependencies and surfaces visual warning badges:
  ```ansi
  TODO
    |-- Architecture Overhaul · 1/3
    |  |-- [x] #1 Setup Database Schema (@dba)
    |  |-- [>] #2 Implement Endpoints (@backend | needs #1) (in_progress)
    |  '-- [ ] #3 Write E2E Tests (@qa | needs #2)
    |        [!] Blocked by pending: #2
    `-----
  ```

### 4. Autonomous Long-Running Tasks & Wake-Up Protocol
- **Zero-Polling Reactive Wakeup**: Guidelines in the Betteragy harness direct the agent to avoid wasteful `sleep` or status polling loops.
- **Autonomous Timer / Cron Arming**: For long-running operations (> 5-10 minutes, e.g., remote builds, large benchmark suites), the agent calls `checkpoint_save` to persist context, then arms `schedule(DurationSeconds=...)` or `schedule(CronExpression=...)` to shut down execution and wake up automatically when the interval elapses.
- **Overnight Execution**: Integrated with the `/goal` command to enable uninterrupted overnight workflows.

### 5. Deep Multi-Angle Reasoning Harness
Installed into `~/.gemini/config/rules/betteragy-harness.md` and `~/.gemini/GEMINI.md`:
- **5-Pillar Analytical Thinking**: First-principles decomposition, multi-case matrix (happy path, edge cases, fault injection, platform quirks), pre-mortem failure analysis, counterfactual skepticism, and falsifiable verification hypotheses.
- **Request Complexity Tiers**: Tier 1 (Atomic: 1-2 tasks), Tier 2 (Features: 2-4 tasks), Tier 3 (Architecture: 4-6 tasks) to eliminate artificial planning bureaucracy on simple requests.
- **Mandatory Proactive Clarification Gate**: Directs the agent to pause and ask structured clarifying questions with recommended options before writing code when requirements or UI choices are ambiguous.
- **Real-Time Color-Coded Progress (Làm tới đâu output tới đó)**: Emits updated ASCII trees in ````ansi blocks at every milestone transition.

### 6. Interactive Rich TUI & Dynamic Theming
- **7 Theming Presets**: **Gruvbox Warm** (Default, tuned for warm terminal backgrounds), **Emerald Forest**, **Cyber Dark**, **Dracula**, **Monokai Pro**, **Nord Arctic**, and **Modern Minimal**.
- **True-Green Quota Progress Bars**: Employs explicit 24-bit TrueColor hex color codes (`#16a34a` / `#22c55e`), guaranteeing that healthy quotas (>= 50%) render as vibrant green across all terminal emulators without teal/cyan mangling.
- **Horizontal Multi-Tab Session Browser**: Seamlessly cycle between concurrent terminal sessions with Left/Right arrow keys or vi navigation (`h` / `l`).

### 7. Offline Token Analytics & Protobuf Decoder
- Direct SQLite extraction from `~/.gemini/antigravity-cli/conversations/*.db`.
- Built-in Protobuf wire decoder extracting Input, Output, Cache, and Thinking tokens (field 10) without running background servers.
- Accurate market pricing calculations for Gemini 3.1 Pro, Gemini 3.8 Flash, and Claude 3.7 Sonnet.

---

## Installation & Quick Start

### 🚀 One-Line Automated Install

**macOS & Linux (Unix):**
```bash
curl -fsSL https://raw.githubusercontent.com/mncuchiinhuttt/betteragy/master/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/mncuchiinhuttt/betteragy/master/install.ps1 | iex
```

---

### Alternative Package Managers

**Via uv (Recommended):**
```bash
uv tool install git+https://github.com/mncuchiinhuttt/betteragy.git
```

**Via pipx:**
```bash
pipx install git+https://github.com/mncuchiinhuttt/betteragy.git
```

**From Source:**
```bash
# Clone the repository
git clone https://github.com/mncuchiinhuttt/betteragy.git
cd betteragy

# Install in editable mode with uv
uv venv
source .venv/bin/activate
uv pip install -e .
```

### 3. Run First-Time Setup Wizard
```bash
betteragy setup
```
The automated 5-step onboarding wizard will:
1. Detect and auto-import existing Antigravity accounts from the system Keychain.
2. Install the deep reasoning harness (`strict` or `balanced`).
3. Register the native `betteragy-todo` MCP server in Antigravity configurations.
4. Set up the autonomous shell alias (`agy -y`).
5. Run full end-to-end system diagnostics.

---

## CLI Command Reference

```bash
# Account Management
betteragy account list                # List all configured accounts, active badges, and tiers
betteragy account switch <id|email>   # Switch active account with proactive token refresh
betteragy account add                 # Connect a new account via OAuth browser loopback
betteragy account add --token <tok>   # Connect headlessly via refresh token
betteragy account remove <id|email>   # Remove an account from the pool

# AI Model Quota Monitoring
betteragy quota                       # Live quota table with True-Green progress bars and countdowns
betteragy quota --watch               # Auto-refreshing quota monitor

# Token Analytics & Cost Telemetry
betteragy usage                       # Total tokens, thinking tokens, and estimated USD cost
betteragy usage --detail              # Model-by-model usage breakdown

# Interactive TUI Switchboard
betteragy                             # Launch full interactive TUI switchboard
betteragy tui                         # Alias for launching TUI

# Auto-Rotation Proxy Daemon
betteragy proxy start                 # Start background MITM auto-rotation proxy
betteragy proxy stop                  # Stop proxy and cleanly revert shell hooks
betteragy proxy status                # Check proxy daemon PID and health status
betteragy proxy run                   # Run proxy in foreground with real-time stream logs

# Task Planning & Multi-Session Watcher
betteragy tasks                       # View active task board
betteragy tasks --watch               # Live auto-updating task watcher with tab navigation
betteragy tasks sessions              # List all execution sessions
betteragy tasks switch <id>           # Switch active execution session

# Reasoning Harness & MCP Registration
betteragy harness install             # Install strict reasoning harness into ~/.gemini
betteragy harness install -p balanced # Install balanced profile
betteragy harness status              # Check current harness installation status
betteragy mcp install                 # Register betteragy-todo in agy MCP configuration
betteragy mcp status                  # Verify MCP server registration

# Autonomous Agent Execution
betteragy agent                       # Launch agy with --effort high and auto-approval (-y)
betteragy agent run "prompt"          # Execute autonomous task non-interactively
```

---

## MCP Server Specification (`betteragy-todo`)

### Stdio Configuration
When registered in `~/.gemini/config/mcp_config.json`:
```json
{
  "mcpServers": {
    "betteragy-todo": {
      "command": "/path/to/betteragy/.venv/bin/python",
      "args": ["-m", "betteragy.mcp.todo_server"],
      "disabled": false
    }
  }
}
```

### Protocol Capabilities
- **Protocol Versions**: `2026-07-28` (SEP-2575 discoverable), `2025-11-25`, `2024-11-05`.
- **JSON-RPC 2.0 Compliant**: Full request/response pairing, structured error codes, and silent handling of notifications without ID.

---

## Architectural Invariants & Engineering Standards

Betteragy adheres to non-negotiable engineering principles:
1. **Strict 200-Line File Limit**: Every Python module and test file is strictly bounded under 200 lines to ensure optimal LLM context loading and high cohesion. Large services are cleanly split into single-responsibility components.
2. **YAGNI, KISS, DRY**: No speculative abstractions or dead code paths. Duplicate logic is abstracted into single-responsibility utility modules (`tree_formatter.py`, `stream_utils.py`).
3. **Clean Cutover**: When refactoring interfaces, all callers are updated atomically; obsolete shims are eliminated.
4. **Zero-Mock Production Code**: Production services execute real system calls, cryptographic operations, and database transactions. Mocks are restricted strictly to unit test boundaries.
5. **Safe Credential Handling**: Private keys and access tokens are managed in memory or encrypted system keyrings with strict file permissions (`0o600`).

---

## Contributing & Development

```bash
# Run the complete test suite (88 automated tests)
pytest

# Verify the 200-line constraint across all files
python3 -c "
import os
for root, _, files in os.walk('.'):
    if any(p in root for p in ['.venv', '.git', '__pycache__', '.pytest_cache']): continue
    for f in files:
        if f.endswith('.py'):
            lines = len(open(os.path.join(root, f)).readlines())
            assert lines <= 200, f'{os.path.join(root, f)} exceeds 200 lines ({lines})'
print('All files verified < 200 lines!')
"
```

---

## License

Distributed under the [MIT License](LICENSE). Built with engineering discipline for the Antigravity developer community.
