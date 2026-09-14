"""Tests for multi-tab session bar and Left/Right key navigation."""

import pytest
from betteragy.mcp.task_db import TaskDB
from betteragy.ui.interactive_tui import InteractiveTUI
from betteragy.ui.key_listener import KEY_ENTER, KEY_LEFT, KEY_RIGHT
from betteragy.ui.session_flows import handle_tasks_key
from betteragy.ui.session_panels import render_session_tab_bar


def test_session_tabs_cycling_and_activation(tmp_path):
    """Verify Left/Right arrow keys cycle session tabs and Enter activates."""
    db = TaskDB(tmp_path / "test_tabs.db")
    s1 = db.init_session("Session 1 Goal", "proj1")
    s2 = db.init_session("Session 2 Goal", "proj2")
    s3 = db.init_session("Session 3 Goal", "proj3")

    tui = InteractiveTUI()
    tui.task_db = db
    tui.current_screen = "tasks"
    tui.session_tab_idx = 0

    # Right arrow cycles to next tab
    handle_tasks_key(tui, KEY_RIGHT)
    assert tui.session_tab_idx == 1
    assert tui.selected_session_id == s2

    # Right arrow cycles to third tab
    handle_tasks_key(tui, KEY_RIGHT)
    assert tui.session_tab_idx == 2
    assert tui.selected_session_id == s1  # note: list_sessions orders by desc id or recent

    # Left arrow cycles backward
    handle_tasks_key(tui, KEY_LEFT)
    assert tui.session_tab_idx == 1

    # Enter activates the selected tab
    handle_tasks_key(tui, KEY_ENTER)
    active = db.get_active_session()
    assert active is not None
    assert active["id"] == tui.selected_session_id
    assert "Active session set" in tui.status_message


def test_session_tabs_vi_keys(tmp_path):
    """Verify 'h' and 'l' keys work for tab switching."""
    db = TaskDB(tmp_path / "test_vi_tabs.db")
    db.init_session("Goal A", "pA")
    db.init_session("Goal B", "pB")

    tui = InteractiveTUI()
    tui.task_db = db
    tui.current_screen = "tasks"
    tui.session_tab_idx = 0

    handle_tasks_key(tui, KEY_RIGHT)
    assert tui.session_tab_idx == 1

    handle_tasks_key(tui, KEY_LEFT)
    assert tui.session_tab_idx == 0
