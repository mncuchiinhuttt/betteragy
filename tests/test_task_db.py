"""Tests for TaskDB SQLite persistence layer."""

import pytest
from betteragy.mcp.task_db import TaskDB


def test_task_db_lifecycle() -> None:
    db = TaskDB(db_path=":memory:")

    # Initial state
    assert db.get_active_session() is None
    assert db.get_tasks() == []

    # Init session
    sess_id = db.init_session(goal="Refactor Database", project_name="betteragy")
    assert sess_id > 0
    active = db.get_active_session()
    assert active is not None
    assert active["goal"] == "Refactor Database"
    assert active["project_name"] == "betteragy"

    # Add tasks
    t1 = db.add_task(title="Write models", priority="high")
    t2 = db.add_task(title="Write migrations", priority="medium")
    assert t1 > 0
    assert t2 > 0

    tasks = db.get_tasks()
    assert len(tasks) == 2
    assert tasks[0]["status"] == "pending"
    assert tasks[0]["priority"] == "high"

    # Update task
    ok = db.update_task(t1, status="in_progress")
    assert ok is True
    assert db.get_tasks()[0]["status"] == "in_progress"

    ok = db.update_task(t1, status="completed", evidence="All 10 tests passed")
    assert ok is True
    updated = db.get_tasks()[0]
    assert updated["status"] == "completed"
    assert updated["evidence"] == "All 10 tests passed"

    # Status filtering
    completed_tasks = db.get_tasks(status_filter="completed")
    assert len(completed_tasks) == 1
    pending_tasks = db.get_tasks(status_filter="pending")
    assert len(pending_tasks) == 1

    # Clear
    cleared = db.clear_tasks()
    assert cleared >= 2
    assert db.get_tasks() == []


def test_task_db_multi_session_isolation() -> None:
    """Verify multiple concurrent sessions maintain isolated task scopes."""
    db = TaskDB(db_path=":memory:")

    # Create Session A
    s_a = db.init_session(goal="Project A Goal", project_name="proj-a", working_dir="/work/a")
    assert s_a > 0
    t_a1 = db.add_task(title="Task A1", session_id=s_a)
    t_a2 = db.add_task(title="Task A2", session_id=s_a)

    # Create Session B
    s_b = db.init_session(goal="Project B Goal", project_name="proj-b", working_dir="/work/b")
    assert s_b > s_a
    t_b1 = db.add_task(title="Task B1", session_id=s_b)

    # Complete a task in session A
    db.update_task(t_a1, status="completed", evidence="Verified A1")

    # Verify session-specific task retrieval
    tasks_a = db.get_tasks(session_id=s_a)
    assert len(tasks_a) == 2
    assert {t["id"] for t in tasks_a} == {t_a1, t_a2}

    tasks_b = db.get_tasks(session_id=s_b)
    assert len(tasks_b) == 1
    assert tasks_b[0]["id"] == t_b1

    # Verify list_sessions statistics
    sessions = db.list_sessions()
    assert len(sessions) == 2
    sess_a_info = next(s for s in sessions if s["id"] == s_a)
    sess_b_info = next(s for s in sessions if s["id"] == s_b)
    assert sess_a_info["total_tasks"] == 2
    assert sess_a_info["completed_tasks"] == 1
    assert sess_b_info["total_tasks"] == 1
    assert sess_b_info["completed_tasks"] == 0

    # Switch active session back to A
    db.set_active_session(s_a)
    active = db.get_active_session()
    assert active is not None
    assert active["id"] == s_a

    # Clear only session B tasks
    db.clear_tasks(session_id=s_b)
    assert len(db.get_tasks(session_id=s_b)) == 0
    assert len(db.get_tasks(session_id=s_a)) == 2

    # Delete session B
    ok = db.delete_session(s_b)
    assert ok is True
    assert db.get_session(s_b) is None
    assert len(db.list_sessions()) == 1

