"""Unit tests for ThemeCatalog, ThemeManager, and dynamic color grading."""

import pytest
from betteragy.ui.theme_catalog import THEME_CATALOG, ThemeDefinition
from betteragy.ui.theme_manager import DEFAULT_THEME_ID, ThemeManager, get_theme_manager
from betteragy.ui.theme import format_status_badge, render_progress_bar
from betteragy.ui.theme_flows import handle_theme_key, render_theme_selector_panel
from betteragy.ui.key_listener import KEY_DOWN, KEY_ENTER, KEY_ESC, KEY_UP
from betteragy.ui.interactive_tui import InteractiveTUI


def test_theme_catalog_completeness():
    """Ensure catalog contains all core themes with required styling attributes."""
    expected_themes = {"warm", "emerald", "cyber", "dracula", "monokai", "nord", "monochrome"}
    assert expected_themes.issubset(set(THEME_CATALOG.keys()))

    for theme_id, th in THEME_CATALOG.items():
        assert th.id == theme_id
        assert th.name != ""
        assert th.primary != ""
        assert th.border_style != ""
        assert th.cursor_style != ""
        assert th.sel_style != ""
        # Quota high must never be blue or cyan
        assert "blue" not in th.quota_high.lower()
        assert "cyan" not in th.quota_high.lower()
        # Rich theme conversion works
        rich_th = th.to_rich_theme()
        assert rich_th is not None


def test_theme_manager_lifecycle():
    """Test theme loading, switching, and invalid fallback."""
    mgr = ThemeManager()
    assert mgr.get_active_theme_id() == DEFAULT_THEME_ID
    assert mgr.get_active_theme().id == "warm"

    # Switch to emerald
    ok = mgr.set_active_theme("emerald")
    assert ok is True
    assert mgr.get_active_theme_id() == "emerald"
    assert mgr.get_active_theme().name == "Emerald Forest"

    # Switch to invalid ID
    bad_ok = mgr.set_active_theme("non_existent_theme")
    assert bad_ok is False
    assert mgr.get_active_theme_id() == "emerald"

    # Restore to warm
    mgr.set_active_theme("warm")
    assert mgr.get_active_theme_id() == "warm"


def test_render_progress_bar_with_theme_override():
    """Verify render_progress_bar respects theme parameter."""
    emerald_th = THEME_CATALOG["emerald"]
    bar_emerald = render_progress_bar(85, width=10, theme=emerald_th)
    assert emerald_th.quota_high in bar_emerald
    assert "85%" in bar_emerald

    dracula_th = THEME_CATALOG["dracula"]
    bar_dracula = render_progress_bar(85, width=10, theme=dracula_th)
    assert dracula_th.quota_high in bar_dracula
    assert "85%" in bar_dracula


def test_format_status_badge_theming():
    """Verify status badges adhere to active theme tokens."""
    warm_th = THEME_CATALOG["warm"]
    active_badge = format_status_badge(is_active=True, is_cooldown=False, disabled=False, theme=warm_th)
    assert "[*] Active" in active_badge
    assert warm_th.quota_high in active_badge

    disabled_badge = format_status_badge(is_active=False, is_cooldown=False, disabled=True, theme=warm_th)
    assert "[x] Disabled" in disabled_badge


def test_theme_flows_panel_and_tui_navigation():
    """Verify theme selector panel rendering and interactive keyboard navigation."""
    mgr = get_theme_manager()
    themes = mgr.list_themes()
    panel = render_theme_selector_panel(themes, selected_idx=0, active_theme_id="warm")
    assert panel is not None

    tui = InteractiveTUI()
    # Enter Themes screen from menu
    tui._dispatch_action("[*] Color Themes")
    assert tui.current_screen == "theme"
    assert tui.theme_idx == 0

    # Navigate down
    handle_theme_key(tui, KEY_DOWN)
    assert tui.theme_idx == 1

    # Apply selected theme (Emerald)
    handle_theme_key(tui, KEY_ENTER)
    assert tui.current_screen == "main"
    assert "Theme switched to" in tui.status_message
    assert mgr.get_active_theme_id() == themes[1].id

    # Reset to warm
    mgr.set_active_theme("warm")
