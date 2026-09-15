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
