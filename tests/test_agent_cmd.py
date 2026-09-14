"""Tests for agent CLI command and alias setup."""

from pathlib import Path
from typer.testing import CliRunner
from betteragy.cli import app

runner = CliRunner()


def test_agent_cmd_help() -> None:
    result = runner.invoke(app, ["agent", "--help"])
    assert result.exit_code == 0
    assert "Launch agy with maximum reasoning effort" in result.stdout


def test_tasks_cmd_help() -> None:
    result = runner.invoke(app, ["tasks", "--help"])
    assert result.exit_code == 0
    assert "View and monitor agy task planning board" in result.stdout


def test_tasks_add_and_clear(tmp_path, monkeypatch) -> None:
    from betteragy.mcp.task_db import TaskDB
    test_db = TaskDB(tmp_path / "cmd_test.db")
    monkeypatch.setattr("betteragy.commands.tasks_cmd.TaskDB", lambda *a, **kw: test_db)

    result = runner.invoke(app, ["tasks", "add", "Test Task", "--priority", "high"])
    assert result.exit_code == 0
    assert "Added task" in result.stdout

    result = runner.invoke(app, ["tasks", "clear"])
    assert result.exit_code == 0
    assert "Cleared" in result.stdout


def test_tasks_sessions_and_switch_cmd(tmp_path, monkeypatch) -> None:
    """Verify tasks sessions list and switch subcommands via CLI."""
    from betteragy.mcp.task_db import TaskDB
    test_db = TaskDB(tmp_path / "cmd_sessions_test.db")
    monkeypatch.setattr("betteragy.commands.tasks_cmd.TaskDB", lambda *a, **kw: test_db)

    # Add a task to create/populate a session
    runner.invoke(app, ["tasks", "add", "Session CLI Task"])

    # List sessions
    res_list = runner.invoke(app, ["tasks", "sessions"])
    assert res_list.exit_code == 0
    assert "Betteragy Task Sessions" in res_list.stdout

    # Switch session
    res_switch = runner.invoke(app, ["tasks", "switch", "1"])
    assert res_switch.exit_code == 0

    # View specific session
    res_view = runner.invoke(app, ["tasks", "--session", "1"])
    assert res_view.exit_code == 0
    assert "Betteragy Task Board" in res_view.stdout

    # Clear specific session
    res_clear = runner.invoke(app, ["tasks", "clear", "--session", "1"])
    assert res_clear.exit_code == 0
    assert "Cleared" in res_clear.stdout


