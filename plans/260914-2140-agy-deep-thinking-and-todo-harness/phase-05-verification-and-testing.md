# Phase 5: Comprehensive Testing & Verification

## Context Links
- Master Plan: [plan.md](file:///Users/vominhlong/betteragy/plans/260914-2140-agy-deep-thinking-and-todo-harness/plan.md)
- Phase 4 Spec: [phase-04-interactive-task-visualizer-tui.md](file:///Users/vominhlong/betteragy/plans/260914-2140-agy-deep-thinking-and-todo-harness/phase-04-interactive-task-visualizer-tui.md)

## Overview
- **Priority**: Medium
- **Current Status**: Pending
- **Brief Description**: Automated unit, integration, and end-to-end verification for the deep thinking harness, MCP To-Do server, and live visualizer.

## Key Insights
- Must verify that `agy` successfully invokes `todo_*` tools without exceptions.
- Must verify that SQLite database writes and reads are atomic and handle concurrent access.
- Must ensure test coverage remains high (>90%) with 0 regression on existing switchboard and quota tests.

## Requirements
### Functional Requirements
- Unit tests for:
  - `HarnessManager` (install, status, backup, uninstall)
  - `TaskDB` (create, read, update status, clear)
  - `Protocol` (JSON-RPC 2.0 requests, batch responses, error handling)
  - `TaskRenderer` (ASCII rendering output format)
- Integration test running mock MCP tool calls over stdio pipe.

### Non-Functional Requirements
- Fast test execution (< 2 seconds total).
- Clean teardown of temporary SQLite files and rule mocks.

## Related Code Files
- Files to create:
  - `tests/test_harness_manager.py`
  - `tests/test_mcp_todo_server.py`
  - `tests/test_task_renderer.py`

## Implementation Steps
1. Write unit tests for `HarnessManager` with temporary rule directories.
2. Write unit tests for `TaskDB` with in-memory SQLite (`:memory:`).
3. Write subprocess pipe test simulating `tools/call` for `todo_add` and `todo_update`.
4. Run full test suite with `pytest`.

## Todo List
- [ ] Write unit tests for harness management
- [ ] Write unit tests for MCP To-Do server
- [ ] Write unit tests for visual renderer
- [ ] Run full pytest suite and verify 100% pass

## Success Criteria
- All tests pass cleanly without errors or warnings.
- Code reviewer agent verifies adherence to guidelines.

## Next Steps
- Review with `code-reviewer` agent.
- Document in `docs/project-changelog.md` and `docs/development-roadmap.md`.
