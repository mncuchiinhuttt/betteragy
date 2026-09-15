"""Regression tests for rendering all InteractiveTUI screens."""

from rich.console import Console

from betteragy.ui.interactive_renderer import build_screen_elements
from betteragy.ui.interactive_tui import InteractiveTUI


ALL_SCREENS = [
    "main",
    "switch_account",
    "remove_account",
    "add_account",
    "oauth_waiting",
    "quota",
    "usage",
    "shell",
    "tasks",
    "session_selector",
    "harness",
    "proxy",
    "theme",
]


def test_build_screen_elements_all_screens():
    """Verify build_screen_elements renders without error across all screens."""
    tui = InteractiveTUI()
    for screen in ALL_SCREENS:
        tui.current_screen = screen
        elements = build_screen_elements(tui)
        assert len(elements) > 0, f"Screen {screen} returned no elements"


def test_main_screen_responsive_widths():
    """Verify main screen renders both narrow (<95) and wide (>=95) layouts."""
    tui = InteractiveTUI()
    tui.current_screen = "main"

    # Narrow width: stacked cards
    tui.console = Console(width=80)
    narrow_elements = build_screen_elements(tui)
    assert len(narrow_elements) == 4

    # Wide width: 2-column layout
    tui.console = Console(width=120)
    wide_elements = build_screen_elements(tui)
    assert len(wide_elements) == 2


def test_filter_flagship_buckets_claude_and_gemini_38():
    """Verify flagship filter prioritizes Claude Sonnet/Opus and newest Gemini 3.8 models."""
    from betteragy.core.models import AccountQuota, QuotaBucket
    from betteragy.ui.dashboard_cards import (
        filter_flagship_buckets,
        format_model_label,
        render_mini_quota_card,
    )

    buckets = [
        QuotaBucket(model_id="chat_20706", display_name="Chat_20706", percentage=100),
        QuotaBucket(model_id="chat_23310", display_name="Chat_23310", percentage=100),
        QuotaBucket(model_id="claude-opus", display_name="Claude Opus 4.6 (Thinking)", percentage=100),
        QuotaBucket(model_id="claude-sonnet", display_name="Claude Sonnet 4.6", percentage=100),
        QuotaBucket(model_id="gemini-2.5-pro", display_name="Gemini 2.5 Pro", percentage=47),
        QuotaBucket(model_id="gemini-3.1-pro", display_name="Gemini 3.1 Pro (High)", percentage=47),
        QuotaBucket(model_id="gemini-3.8-high", display_name="Gemini 3.8 Flash (High)", percentage=47),
        QuotaBucket(model_id="gemini-3.8-med", display_name="Gemini 3.8 Flash (Medium)", percentage=47),
    ]

    selected = filter_flagship_buckets(buckets, limit=4)
    names = [b.display_name for b in selected]
    assert "Claude Sonnet 4.6" in names
    assert "Claude Opus 4.6 (Thinking)" in names
    assert "Gemini 3.8 Flash (High)" in names
    assert "Gemini 3.8 Flash (Medium)" in names
    assert "Chat_20706" not in names

    assert format_model_label("Claude Opus 4.6 (Thinking)") == "Claude Opus 4.6"
    assert format_model_label("Gemini 3.8 Flash (High)") == "Gemini 3.8 Flash High"

    quota = AccountQuota(email="test@user.com", buckets=buckets)
    panel = render_mini_quota_card(quota)
    assert panel is not None

