"""Tests for ASCII task board renderer."""

import pytest
from rich.panel import Panel
from betteragy.mcp.task_db import TaskDB
from betteragy.ui.session_panels import render_session_tab_bar
from betteragy.ui.task_renderer import render_ascii_task_board, render_sessions_table


def test_task_renderer_empty_and_populated() -> None:
    db = TaskDB(db_path=":memory:")

    # Empty render
    panel = render_ascii_task_board(db)
    assert isinstance(panel, Panel)

    # Populated render
    s1 = db.init_session("Implement Authentication", "auth-service")
    db.add_task("Write PKCE flow", priority="high", session_id=s1)
    db.add_task("Verify JWT signatures", priority="medium", session_id=s1)
    db.update_task(1, status="completed", evidence="All unit tests pass")

    populated_panel = render_ascii_task_board(db, session_id=s1)
    assert isinstance(populated_panel, Panel)


def test_render_sessions_table() -> None:
    """Verify session table renders correctly for empty and populated states."""
    # Empty
    p_empty = render_sessions_table([])
    assert isinstance(p_empty, Panel)

    # Populated
    sessions = [
        {
            "id": 1,
            "goal": "Build Agent",
            "project_name": "betteragy",
            "is_active": 1,
            "total_tasks": 5,
            "completed_tasks": 3,
        },
        {
            "id": 2,
            "goal": "Write Docs",
            "project_name": "docs",
            "is_active": 0,
            "total_tasks": 2,
            "completed_tasks": 0,
        },
    ]
    p_pop = render_sessions_table(sessions, active_id=1)
    assert isinstance(p_pop, Panel)


def test_render_session_tab_bar() -> None:
    """Verify session tab bar formatting and sliding window."""
    # Empty sessions
    bar_empty = render_session_tab_bar([])
    assert str(bar_empty) == ""

    # Few sessions
    sessions = [
        {"id": 1, "project_name": "repo1", "total_tasks": 3, "completed_tasks": 3, "is_active": 1},
        {"id": 2, "project_name": "repo2", "total_tasks": 2, "completed_tasks": 1, "is_active": 0},
    ]
    bar = render_session_tab_bar(sessions, current_session_id=1)
    bar_text = str(bar)
    assert "#1 repo1 (100%)" in bar_text
    assert "#2 repo2 (50%)" in bar_text

    # Many sessions sliding window
    many = [{"id": i, "project_name": f"p{i}", "total_tasks": 1, "completed_tasks": 0} for i in range(1, 10)]
    bar_many = render_session_tab_bar(many, current_session_id=8, max_visible=3)
    assert "[Right >]" in str(bar_many) or "[< Left]" in str(bar_many)


