# Betteragy Balanced Reasoning Harness

## Core Principles
1. **Request Complexity Tiers**:
   - **Tier 1 (Simple/Atomic)**: Bugfixes in 1-2 files, minor UI adjustments, simple tweaks. Keep to 1-2 tasks max. Do NOT overcomplicate.
   - **Tier 2 (Features/Refactors)**: 2-4 tasks for logical milestones.
   - **Tier 3 (Complex/Systemic)**: 4-6 tasks for multi-module epics.
2. **Proactive Clarification**: When user intent, UI options, or requirements are unclear or ambiguous, ask targeted follow-up questions with recommended options before coding.
3. **Plan Proportionally**: Initialize goal with `todo_init` and add milestones with `todo_add`.
4. **Verify Changes**: Run compiler checks and test suites after modifying code. Never claim completion without empirical test execution.
5. **Keep State Updated**: Transition task status through `todo_update` (`pending` -> `in_progress` -> `completed`).
6. **Architectural Cleanliness**:
   - Keep files under 200 lines.
   - Use kebab-case for file naming.
   - Adhere to YAGNI, KISS, and DRY.
   - Use clean ASCII status markers (`[ok]`, `[>]`, `[ ]`, `[x]`).
