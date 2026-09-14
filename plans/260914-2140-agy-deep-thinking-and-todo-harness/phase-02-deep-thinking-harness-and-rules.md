# Phase 2: Deep Thinking & Rigorous Verification Harness Injection

## Context Links
- Master Plan: [plan.md](file:///Users/vominhlong/betteragy/plans/260914-2140-agy-deep-thinking-and-todo-harness/plan.md)
- Phase 1 Spec: [phase-01-architecture-tradeoffs-and-spec.md](file:///Users/vominhlong/betteragy/plans/260914-2140-agy-deep-thinking-and-todo-harness/phase-01-architecture-tradeoffs-and-spec.md)

## Overview
- **Priority**: High
- **Current Status**: Pending
- **Brief Description**: Design and implement the prompt harness engine in `betteragy` that installs, activates, and synchronizes specialized thinking directives and verification protocols into `agy`'s configuration (`~/.gemini/config/rules/betteragy-harness.md`).

## Key Insights
- `agy` reads markdown rule files in `~/.gemini/config/rules/` and embeds them as `<RULE[user_global]>`.
- By providing a structured, enforceable protocol, LLMs can be constrained to:
  1. **Phase 1: Explore & Analyze (No Immediate Edits)**: Must inspect existing code, verify assumptions, check syntax.
  2. **Phase 2: Task Planning**: Must decompose the task into atomic subtasks using the To-Do tool.
  3. **Phase 3: Disciplined Execution**: One subtask at a time, keeping files under 200 lines, strictly following YAGNI/KISS/DRY.
  4. **Phase 4: Automated Verification Gate**: Compile check, syntax check, test run before marking a task done.
  5. **Phase 5: Self-Reflection & Evidence Reporting**: Emitting concrete proof of verification rather than vague claims.

## Requirements
### Functional Requirements
- CLI command `betteragy harness install` / `betteragy harness status` / `betteragy harness uninstall`.
- Configurable reasoning profiles:
  - `--strict`: Maximum verification, mandatory compile checks, no assumptions.
  - `--balanced`: Standard disciplined coding workflow.
  - `--fast`: Lightweight checking.
- Auto-injection of `--effort high` flag wrapper when running `agy`.

### Non-Functional Requirements
- Modular templates under 200 lines per file.
- Clean uninstallation without corrupting existing user rules.

## Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    betteragy CLI                            │
│           betteragy harness enable --strict                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
            ┌────────────────────────────────────┐
            │   HarnessManager (Python)          │
            │   - Validates template integrity   │
            │   - Backs up existing rules        │
            │   - Atomic file write with 0644    │
            └──────────────────┬─────────────────┘
                               │
                               ▼
        ┌────────────────────────────────────────────┐
        │ ~/.gemini/config/rules/betteragy-harness.md│
        │ <RULE[user_global]>                        │
        │ - Deep Reasoning Protocol (5 Phases)       │
        │ - Verification Gates                       │
        │ - Mandatory To-Do Tracking Directives      │
        └────────────────────────────────────────────┘
```

## Related Code Files
- Files to create:
  - `src/betteragy/harness/__init__.py`
  - `src/betteragy/harness/harness_manager.py`
  - `src/betteragy/harness/templates/deep_thinking_rule.py`
  - `src/betteragy/commands/harness_cmd.py`
- Files to modify:
  - `src/betteragy/cli.py`

## Implementation Steps
1. Create `src/betteragy/harness/templates/deep_thinking_rule.py` containing the structured markdown harness.
2. Build `HarnessManager` with `install()`, `uninstall()`, `status()`, and backup logic.
3. Wire `harness` command group into Typer CLI: `betteragy harness [install|status|uninstall]`.

## Todo List
- [ ] Implement template generator with strict reasoning constraints
- [ ] Implement `HarnessManager` with atomic writes
- [ ] Add CLI commands in `harness_cmd.py`
- [ ] Write unit tests for rule installation and idempotency

## Success Criteria
- Running `betteragy harness install` writes the rule cleanly to `~/.gemini/config/rules/betteragy-harness.md`.
- `agy` immediately picks up the new global rules without requiring a restart.

## Risk Assessment
- **Risk**: Rule conflicts with existing user rules.
- **Mitigation**: Unique filename `betteragy-harness.md` with explicit priority markers; provide non-destructive rollback.

## Security Considerations
- Ensure template strings are statically defined and cannot execute arbitrary shell commands during template rendering.

## Next Steps
- Implement Phase 3: MCP To-Do Service & Tools.
