"""CLI commands for viewing and watching the task planning board."""

import time
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live

from betteragy.mcp.task_db import TaskDB
from betteragy.ui.key_listener import KEY_ENTER, KEY_ESC, KEY_LEFT, KEY_QUIT, KEY_RIGHT, KeyListener
from betteragy.ui.session_panels import render_sessions_table
from betteragy.ui.task_renderer import render_ascii_task_board

tasks_app = typer.Typer(help="View and monitor agy task planning board.")
console = Console()


def _run_live_watch(db: TaskDB, session_id: Optional[int], console: Console) -> None:
    """Run real-time task board watcher with Left/Right tab switching."""
    cur_session_id = session_id
    console.print("[dim]Watching Betteragy Task Board (<- / -> Switch Tab, Enter Set Active, q Exit)...[/]")
    try:
        with KeyListener() as listener:
            with Live(render_ascii_task_board(db, session_id=cur_session_id), console=console, refresh_per_second=4) as live:
                while True:
                    key = listener.read_key()
                    if key in (KEY_QUIT, KEY_ESC):
                        break
                    if key in (KEY_LEFT, KEY_RIGHT):
                        sessions = db.list_sessions(limit=20)
                        if sessions:
                            cur_idx = 0
                            for idx, s in enumerate(sessions):
                                if s["id"] == cur_session_id:
                                    cur_idx = idx
                                    break
                            delta = -1 if key == KEY_LEFT else 1
                            cur_session_id = sessions[(cur_idx + delta) % len(sessions)]["id"]
                            live.update(render_ascii_task_board(db, session_id=cur_session_id))
                    elif key == KEY_ENTER and cur_session_id:
                        db.set_active_session(cur_session_id)
                    time.sleep(0.2)
                    live.update(render_ascii_task_board(db, session_id=cur_session_id))
    except KeyboardInterrupt:
        pass
    finally:
        console.print("\n[dim]Stopped watching tasks.[/]")


@tasks_app.callback(invoke_without_command=True)
def default_tasks(
    ctx: typer.Context,
    session_id: Optional[int] = typer.Option(None, "--session", "-s", help="Session ID to inspect."),
    watch: bool = typer.Option(False, "--watch", "-w", help="Live watch task updates in real-time."),
) -> None:
    """Display active task board or watch live updates with interactive tabs."""
    if ctx.invoked_subcommand is not None:
        return

    db = TaskDB()
    if not watch:
        console.print(render_ascii_task_board(db, session_id=session_id))
        return

    _run_live_watch(db, session_id, console)


@tasks_app.command("sessions")
def list_sessions(
    limit: int = typer.Option(20, "--limit", "-l", help="Max sessions to list."),
) -> None:
    """List all planning sessions and their verification progress."""
    db = TaskDB()
    sessions = db.list_sessions(limit=limit)
    console.print(render_sessions_table(sessions))


@tasks_app.command("switch")
def switch_session(
    session_id: int = typer.Argument(..., help="ID of session to set as active."),
) -> None:
    """Switch active session focus."""
    db = TaskDB()
    ok = db.set_active_session(session_id)
    if ok:
        sess = db.get_session(session_id)
        goal = sess["goal"] if sess else ""
        console.print(f"[bold green][ok] Active session switched to #{session_id} ('{goal}')[/bold green]")
    else:
        console.print(f"[bold red][x] Session #{session_id} not found.[/bold red]")


@tasks_app.command("watch")
def watch_tasks(
    session_id: Optional[int] = typer.Option(None, "--session", "-s", help="Session ID to watch."),
) -> None:
    """Watch task planning board in real time with interactive tab switching."""
    db = TaskDB()
    _run_live_watch(db, session_id, console)


@tasks_app.command("clear")
def clear_tasks(
    session_id: Optional[int] = typer.Option(None, "--session", "-s", help="Session ID to clear tasks for."),
) -> None:
    """Clear tasks from the planning board."""
    db = TaskDB()
    count = db.clear_tasks(session_id=session_id)
    target = f"from session #{session_id}" if session_id is not None else "from all sessions"
    console.print(f"[bold yellow][ok] Cleared {count} task(s) {target}.[/]")


@tasks_app.command("add")
def add_task(
    title: str = typer.Argument(..., help="Title of task to add"),
    priority: str = typer.Option("medium", "--priority", "-p", help="Priority (high/medium/low)"),
    session_id: Optional[int] = typer.Option(None, "--session", "-s", help="Session ID to add to."),
) -> None:
    """Manually add a task to the board."""
    db = TaskDB()
    task_id = db.add_task(title=title, priority=priority, session_id=session_id)
    sid_str = f" (session #{session_id})" if session_id else ""
    console.print(f"[bold green][ok] Added task #{task_id}{sid_str}: '{title}'[/]")
