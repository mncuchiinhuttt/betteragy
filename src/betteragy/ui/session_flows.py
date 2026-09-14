"""Session navigation flows and interactive key handlers for Betteragy TUI."""

from typing import Any
from .key_listener import KEY_BACK, KEY_DOWN, KEY_ENTER, KEY_ESC, KEY_LEFT, KEY_QUIT, KEY_REFRESH, KEY_RIGHT, KEY_UP
from .session_panels import render_session_selector_panel, render_session_tab_bar, render_sessions_table


def handle_tasks_key(tui: Any, key: str) -> bool:
    """Handle keypresses on the tasks screen with Left/Right tab switching."""
    if key == KEY_QUIT:
        return True
    if key in (KEY_ESC, KEY_BACK):
        tui.current_screen = "main"
        return False

    sessions = tui.task_db.list_sessions(limit=20)
    if not sessions:
        return False

    if not hasattr(tui, "session_tab_idx"):
        tui.session_tab_idx = 0

    if key == KEY_LEFT:
        tui.session_tab_idx = (tui.session_tab_idx - 1) % len(sessions)
        tui.selected_session_id = sessions[tui.session_tab_idx]["id"]
    elif key == KEY_RIGHT:
        tui.session_tab_idx = (tui.session_tab_idx + 1) % len(sessions)
        tui.selected_session_id = sessions[tui.session_tab_idx]["id"]
    elif key == KEY_ENTER:
        cur_id = getattr(tui, "selected_session_id", None) or sessions[tui.session_tab_idx]["id"]
        tui.task_db.set_active_session(cur_id)
        tui.status_message = f"[bold green][ok] Active session set to #{cur_id}[/bold green]"
    elif key in ("s", "S"):
        tui.current_screen = "session_selector"
        tui.session_idx = tui.session_tab_idx
    return False


def handle_session_selector_key(tui: Any, key: str) -> bool:
    """Handle keypresses on the session selector screen."""
    sessions = tui.task_db.list_sessions(limit=20)
    if not sessions:
        tui.current_screen = "tasks"
        return False

    if key in (KEY_UP, KEY_DOWN):
        delta = -1 if key == KEY_UP else 1
        tui.session_idx = (tui.session_idx + delta) % len(sessions)
    elif key in (KEY_ESC, KEY_BACK):
        tui.current_screen = "tasks"
    elif key == KEY_QUIT:
        return True
    elif key == KEY_ENTER:
        target = sessions[tui.session_idx]
        tui.task_db.set_active_session(target["id"])
        tui.selected_session_id = target["id"]
        tui.session_tab_idx = tui.session_idx
        tui.status_message = f"[bold green][ok] Active session switched to #{target['id']}[/bold green]"
        tui.current_screen = "tasks"
    return False
