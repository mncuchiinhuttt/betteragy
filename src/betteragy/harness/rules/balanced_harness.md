# Betteragy Balanced Reasoning Harness

## Core Principles
1. **Plan First**: Always decompose non-trivial tasks into atomic milestones using `todo_init` and `todo_add`.
2. **Verify Changes**: Run compiler checks and test suites after modifying code. Never claim completion without test execution.
3. **Keep State Updated**: Transition task status through `todo_update` (`pending` -> `in_progress` -> `completed`).
4. **Architectural Cleanliness**:
   - Keep files under 200 lines.
   - Use kebab-case for file naming.
   - Adhere to YAGNI, KISS, and DRY.
   - Use clean ASCII status markers (`[ok]`, `[>]`, `[ ]`, `[x]`).
