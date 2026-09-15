"""Tests for ASCII and ANSI color-coded task tree formatting and live progress reporting."""

import pytest
from betteragy.mcp.task_db import TaskDB
from betteragy.mcp.todo_tools import execute_tool, format_tasks_ascii_tree


def test_format_tasks_plain_ascii():
    tasks = [
        {"id": 1, "title": "Task 1", "status": "completed", "evidence": "78 passed"},
        {"id": 2, "title": "Task 2", "status": "in_progress", "evidence": ""},
        {"id": 3, "title": "Task 3", "status": "pending", "evidence": ""},
        {"id": 4, "title": "Task 4", "status": "blocked", "evidence": ""},
    ]
    tree = format_tasks_ascii_tree(
        goal="Feature Work",
        tasks=tasks,
        project_name="betteragy",
        use_color=False,
    )
    assert "TODO" in tree
    assert "Feature Work (betteragy) · 1/4" in tree
    assert "[x] #1 Task 1" in tree
    assert "Evidence: 78 passed" in tree
    assert "[>] #2 Task 2 (in_progress)" in tree
    assert "[ ] #3 Task 3" in tree
    assert "[!] #4 Task 4 (blocked)" in tree
    assert "\033[" not in tree


def test_format_tasks_ansi_color():
    tasks = [
        {"id": 1, "title": "Task 1", "status": "completed", "evidence": "All tests pass"},
        {"id": 2, "title": "Task 2", "status": "in_progress", "evidence": ""},
        {"id": 3, "title": "Task 3", "status": "pending", "evidence": ""},
        {"id": 4, "title": "Task 4", "status": "blocked", "evidence": ""},
    ]
    tree = format_tasks_ascii_tree(
        goal="Feature Work",
        tasks=tasks,
        project_name="betteragy",
        use_color=True,
    )
    # Check ANSI codes
    assert "\033[1;32m[x]\033[0m" in tree  # Green for completed
    assert "\033[1;33m[>]\033[0m" in tree  # Yellow for in_progress
    assert "\033[0;90m[ ]\033[0m" in tree  # Dim for pending
    assert "\033[1;31m[!]\033[0m" in tree  # Red for blocked
    assert "\033[1;36mTODO\033[0m" in tree  # Cyan header
    assert "Evidence: All tests pass" in tree


def test_tool_live_tree_reporting(tmp_path):
    db_path = tmp_path / "test_tasks.db"
    db = TaskDB(db_path=db_path)
    sid = db.init_session("Live Progress Session", "live-proj")

    # Add task with color=True
    res_add = execute_tool(
        "todo_add",
        {"title": "Implement Feature", "session_id": sid, "color": True},
        db,
    )
    assert "Added task #1" in res_add["content"][0]["text"]
    assert "\033[1;36mTODO\033[0m" in res_add["content"][0]["text"]
    assert "[ ]" in res_add["content"][0]["text"]

    # Update task to in_progress with color=True
    res_up = execute_tool(
        "todo_update",
        {"task_id": 1, "status": "in_progress", "session_id": sid, "color": True},
        db,
    )
    assert "Task #1 updated to 'in_progress'" in res_up["content"][0]["text"]
    assert "\033[1;33m[>]\033[0m" in res_up["content"][0]["text"]

    # Update task to completed with evidence and color=True
    res_done = execute_tool(
        "todo_update",
        {
            "task_id": 1,
            "status": "completed",
            "evidence": "100% pass",
            "session_id": sid,
            "color": True,
        },
        db,
    )
    assert "Task #1 updated to 'completed'" in res_done["content"][0]["text"]
    assert "\033[1;32m[x]\033[0m" in res_done["content"][0]["text"]
    assert "Evidence: 100% pass" in res_done["content"][0]["text"]
