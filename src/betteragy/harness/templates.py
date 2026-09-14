"""Prompt harness templates for deep reasoning and verification in agy."""

from pathlib import Path

RULES_DIR = Path(__file__).parent / "rules"

FALLBACK_STRICT = """# Betteragy Elite Reasoning & Verification Harness

## Core Directives
1. **Never Guess - Always Verify**: Run commands to prove facts before touching code.
2. **Mandatory Task Planning**: Use `todo_init` and `todo_add` to decompose requests into subtasks.
3. **Atomic Execution**: Focus on 1 task at a time; mark `in_progress` via `todo_update`.
4. **Verification Gates**: Run compilation checks and unit tests before marking `completed`.
5. **Code Standards**: Keep files under 200 lines, use kebab-case, follow YAGNI/KISS/DRY.
"""

FALLBACK_BALANCED = """# Betteragy Balanced Reasoning Harness

## Directives
1. **Plan First**: Call `todo_add` to break requests into logical milestones.
2. **Verify Code**: Always check syntax and compile code after making changes.
3. **Maintain Task Status**: Update task status with `todo_update` as you make progress.
4. **Concise Quality**: Write clean code, keep files under 200 lines.
"""


def get_harness_template(profile: str = "strict") -> str:
    """Return harness template based on profile."""
    profile_lower = profile.lower().strip()
    target_file = RULES_DIR / f"{profile_lower}_harness.md"

    if target_file.exists():
        try:
            return target_file.read_text(encoding="utf-8")
        except OSError:
            pass

    if profile_lower == "balanced":
        return FALLBACK_BALANCED
    return FALLBACK_STRICT
