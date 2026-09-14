# Phase 4: Real-time ASCII Task Visualizer & Agent Super-Harness

## Context Links
- Master Plan: [plan.md](file:///Users/vominhlong/betteragy/plans/260914-2140-agy-deep-thinking-and-todo-harness/plan.md)
- Phase 3 Spec: [phase-03-mcp-todo-service-and-tools.md](file:///Users/vominhlong/betteragy/plans/260914-2140-agy-deep-thinking-and-todo-harness/phase-03-mcp-todo-service-and-tools.md)

## Overview
- **Priority**: High
- **Current Status**: Pending
- **Brief Description**: Design and implement the visual task tracking interface and outer agent launcher (`betteragy agent [prompt]`), rendering a live ASCII Kanban / Checklist widget in the terminal synchronized with `~/.config/betteragy/tasks.db`.

## Key Insights
- Users desire clear visual feedback on what the agent is currently working on, what steps are done, and what is pending (similar to Claude Code's interactive task list or Manus).
- By decoupling the task store (`tasks.db`) via SQLite WAL mode, `betteragy` can render a live ASCII task panel either:
  1. Inside the existing Betteragy TUI as a dedicated "Tasks" screen (`[3] Tasks & Planning`).
  2. In a standalone live watcher CLI command: `betteragy tasks --watch`.
  3. Through `betteragy agent`: a unified launcher that automatically applies `--effort high`, launches `agy`, and displays the active task list.

## Requirements
### Functional Requirements
- ASCII task list renderer following clean ASCII formatting guidelines:
  - `[ ]` Pending
  - `[>]` In Progress
  - `[ok]` Completed / Verified
  - `[x]` Blocked / Failed
- Live watch mode with 1-second debounce (`betteragy tasks --watch`).
- Interactive TUI Screen integrated into `src/betteragy/ui/interactive_screens.py`.
- Subcommand `betteragy agent` to launch `agy` with high reasoning effort and configured harness.

### Non-Functional Requirements
- Maintain < 200 lines per module.
- 0 double-width emoji characters to prevent terminal rendering artifacts.
- Non-blocking database reads using SQLite read-only connection.

## Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                       Tasks Database                        │
│                ~/.config/betteragy/tasks.db                 │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Read-only polling / WAL)
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌───────────────────────────┐         ┌───────────────────────────┐
│ betteragy tasks --watch   │         │ betteragy TUI             │
│ (Standalone Terminal Pane)│         │ Screen 3: Tasks & Harness │
│                           │         │                           │
│ [~] ACTIVE GOAL: Refactor │         │ [~] ACTIVE GOAL: Refactor │
│ [ok] 1. Inspect files     │         │ [ok] 1. Inspect files     │
│ [>]  2. Implement tests   │         │ [>]  2. Implement tests   │
│ [ ]  3. Verify compile    │         │ [ ]  3. Verify compile    │
└───────────────────────────┘         └───────────────────────────┘
```

## Related Code Files
- Files to create:
  - `src/betteragy/ui/task_renderer.py`
  - `src/betteragy/commands/tasks_cmd.py`
  - `src/betteragy/commands/agent_cmd.py`
- Files to modify:
  - `src/betteragy/ui/interactive_screens.py`
  - `src/betteragy/ui/interactive_renderer.py`
  - `src/betteragy/cli.py`

## Implementation Steps
1. Create `task_renderer.py` using Rich Table / Panel with ASCII markers.
2. Implement `tasks_cmd.py` (`betteragy tasks` and `betteragy tasks --watch`).
3. Add "Tasks" tab to the interactive TUI menu.
4. Implement `agent_cmd.py` (`betteragy agent`) to execute `agy` with automated reasoning flags.

## Todo List
- [ ] Create `task_renderer.py` with ASCII markers
- [ ] Implement `betteragy tasks` CLI commands
- [ ] Integrate Task Screen into TUI
- [ ] Implement `betteragy agent` launcher
- [ ] Write unit tests for task rendering

## Success Criteria
- User can see live task progress in real time as the agent works.
- Rendering works cleanly across standard terminals without character clipping.

## Risk Assessment
- **Risk**: Terminal resizing or flicker during live watch.
- **Mitigation**: Use `rich.live.Live` with `transient=False` and clean screen repaints.

## Security Considerations
- Read-only queries to `tasks.db` to prevent lock contention.

## Next Steps
- Implement Phase 5: Verification & End-to-End Testing.
