"""Prompt harness templates for deep reasoning and verification in agy."""

from pathlib import Path

RULES_DIR = Path(__file__).parent / "rules"

FALLBACK_STRICT = """# Betteragy Elite Reasoning & Verification Harness

## Core Directives
1. **Never Guess - Clarify & Verify**: If requirements are unclear or have choices, ask the user first. Run commands to prove facts.
2. **Request Complexity Tiers**:
   - Tier 1 (Simple/Atomic): 1-2 tasks max. Do NOT create bloated checklists.
   - Tier 2 (Features): 2-4 tasks for logical milestones.
   - Tier 3 (Complex): 4-6 tasks for multi-module epics.
3. **Proportional Planning**: Use `todo_init` and `todo_add` matching the tier.
4. **Verification Gates**: Run compilation checks and unit tests before marking `completed`.
5. **Code Standards**: Keep files under 200 lines, use kebab-case, follow YAGNI/KISS/DRY.
"""

FALLBACK_BALANCED = """# Betteragy Balanced Reasoning Harness

## Directives
1. **Request Tiers**: Tier 1 (1-2 tasks), Tier 2 (2-4 tasks), Tier 3 (4-6 tasks).
2. **Clarify Unclear Points**: Ask targeted follow-up questions when requirements have multiple options.
3. **Plan Proportionally**: Call `todo_init` and `todo_add` without unnecessary task bureaucracy.
4. **Verify Code**: Always check syntax and run tests after modifications.
5. **Concise Quality**: Write clean code, keep files under 200 lines.
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
