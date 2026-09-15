"""Session navigation flows and interactive key handlers for Betteragy TUI."""

from typing import Any
from .key_listener import KEY_BACK, KEY_DOWN, KEY_ENTER, KEY_ESC, KEY_LEFT, KEY_QUIT, KEY_REFRESH, KEY_RIGHT, KEY_UP
from .session_panels import render_session_selector_panel, render_session_tab_bar, render_sessions_table


def handle_tasks_key(tui: Any, key: str) -> bool:
    """Handle keypresses on the tasks screen: task navigation, status toggle, clean tasks, tab switching."""
    if key == KEY_QUIT:
        return True
    if key in (KEY_ESC, KEY_BACK):
        tui.current_screen = "main"
        tui.status_message = ""
        return False

    sessions = tui.task_db.list_sessions(limit=20)
    cur_sess_id = getattr(tui, "selected_session_id", None)
    if cur_sess_id is None and sessions:
        cur_sess_id = sessions[0]["id"]

    tasks = tui.task_db.get_tasks(session_id=cur_sess_id) if cur_sess_id else []
    if not hasattr(tui, "task_idx"):
        tui.task_idx = 0
    if tasks and tui.task_idx >= len(tasks):
        tui.task_idx = max(0, len(tasks) - 1)

    if key in ("c", "C"):
        if cur_sess_id:
            count = tui.task_db.clear_tasks(session_id=cur_sess_id)
            tui.task_idx = 0
            tui.status_message = f"[bold yellow][ok] Cleared {count} task(s) in Session #{cur_sess_id}[/bold yellow]"
        return False

    if key in (KEY_UP, "k", "K"):
        if tasks:
            tui.task_idx = (tui.task_idx - 1) % len(tasks)
        return False
    if key in (KEY_DOWN, "j", "J"):
        if tasks:
            tui.task_idx = (tui.task_idx + 1) % len(tasks)
        return False

    if key in (" ", KEY_ENTER):
        if tasks and 0 <= tui.task_idx < len(tasks):
            t = tasks[tui.task_idx]
            nxt = {"pending": "in_progress", "in_progress": "completed", "completed": "blocked", "blocked": "pending"}.get(t["status"], "pending")
            tui.task_db.update_task(t["id"], status=nxt)
            tui.status_message = f"[bold green][ok] Task #{t['id']} -> [{nxt}][/bold green]"
        elif cur_sess_id:
            tui.task_db.set_active_session(cur_sess_id)
            tui.status_message = f"[bold green][ok] Active session set to #{cur_sess_id}[/bold green]"
        return False

    if sessions:
        if not hasattr(tui, "session_tab_idx"):
            tui.session_tab_idx = 0
        if key == KEY_LEFT:
            tui.session_tab_idx = (tui.session_tab_idx - 1) % len(sessions)
            tui.selected_session_id = sessions[tui.session_tab_idx]["id"]
            tui.task_idx = 0
        elif key == KEY_RIGHT:
            tui.session_tab_idx = (tui.session_tab_idx + 1) % len(sessions)
            tui.selected_session_id = sessions[tui.session_tab_idx]["id"]
            tui.task_idx = 0

    if key in ("s", "S"):
        tui.current_screen = "session_selector"
        tui.session_idx = getattr(tui, "session_tab_idx", 0)
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
