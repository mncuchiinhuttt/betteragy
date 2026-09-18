"""ASCII Task visualizer renderer for Betteragy."""

from typing import Any, Dict, List, Optional

from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from betteragy.mcp.task_db import TaskDB
from .session_panels import render_session_tab_bar, render_sessions_table


def render_ascii_task_board(
    db: TaskDB | None = None,
    session_id: Optional[int] = None,
    selected_task_idx: Optional[int] = None,
) -> RenderableType:
    db = db or TaskDB()
    sessions = db.list_sessions(limit=10)
    session = db.get_session(session_id) if session_id is not None else db.get_active_session()
    if not session and sessions:
        session = sessions[0]

    tasks = db.get_tasks(session_id=session["id"] if session else None)
    tab_bar = render_session_tab_bar(sessions, session["id"] if session else None)

    sid_str = f" [Session #{session['id']}]" if session else ""
    goal = session["goal"] if session else "No active planning session"
    project = f" ({session['project_name']})" if session and session.get("project_name") else ""

    if not tasks:
        empty_grid = Table.grid(padding=(0, 0))
        if sessions:
            empty_grid.add_row(tab_bar)
            empty_grid.add_row(Text(""))
        empty_grid.add_row(Text.from_markup(
            f"[bold cyan][~] GOAL{sid_str}:[/] {goal}{project}\n\n"
            f"[dim]No tasks created yet for this session.[/]"
        ))
        return Panel(
            empty_grid,
            title="[bold cyan]◉ Betteragy Task Board[/bold cyan]",
            subtitle="[dim]←/→ Switch Tab  |  [s] Sessions  |  [c] Clear Tasks[/dim]",
            border_style="cyan",
        )

    completed_count = sum(1 for t in tasks if t["status"] == "completed")
    total_count = len(tasks)
    pct = int((completed_count / total_count) * 100) if total_count > 0 else 0

    bar_len = 24
    filled_len = int(bar_len * (pct / 100))
    progress_bar = f"\\[{'#' * filled_len}{'-' * (bar_len - filled_len)}]"

    table = Table(show_header=True, header_style="bold white", box=None, padding=(0, 1))
    table.add_column("Chip", width=4, justify="center")
    table.add_column("Status", width=6, justify="center")
    table.add_column("ID", width=4, justify="right", style="dim")
    table.add_column("Task Title", ratio=1, no_wrap=True)
    table.add_column("Priority", width=8, justify="center")
    status_styles = {
        "pending": ("◻", "dim white"),
        "in_progress": ("◼", "bold yellow"),
        "completed": ("✔", "bold green"),
        "blocked": ("✕", "bold red"),
    }
    sel_task = None
    for i, t in enumerate(tasks):
        is_sel = selected_task_idx is not None and i == selected_task_idx
        if is_sel:
            sel_task = t
        cursor = "❯" if is_sel else " "
        icon, style = status_styles.get(t["status"], ("·", "white"))
        status_cell = Text(icon, style="bold cyan" if is_sel else style)
        title_text = Text(t["title"], style="bold cyan" if is_sel else style)
        pri_color = {"high": "bold red", "medium": "yellow", "low": "cyan"}.get(t["priority"], "white")
        pri_cell = Text(t["priority"].upper(), style=pri_color)
        row_style = "bold white on #060d42" if is_sel else None
        table.add_row(cursor, status_cell, str(t["id"]), title_text, pri_cell, style=row_style)
    summary_text = (
        f"[bold cyan][~] GOAL{sid_str}:[/] [bold white]{goal}[/]{project}\n"
        f"[dim]Progress:[/] [green]{progress_bar}[/] [bold white]{pct}%[/] "
        f"([cyan]{completed_count}/{total_count}[/] tasks verified)\n"
    )
    content = Table.grid(padding=(0, 0))
    if sessions:
        content.add_row(tab_bar)
        content.add_row(Text(""))
    content.add_row(summary_text)
    content.add_row(table)
    if sel_task and (sel_task.get("evidence") or sel_task.get("description")):
        detail = Text("\n⎿ Execution Detail: ", style="bold cyan")
        detail.append(sel_task.get("evidence") or sel_task.get("description") or "", style="dim green" if sel_task.get("evidence") else "dim")
        content.add_row(detail)

    return Panel(
        content,
        title="[bold cyan]◉ Betteragy Task Board[/bold cyan]",
        subtitle=f"[dim]↑/↓ Select Task  |  Space Toggle Status  |  [c] Clear Tasks  |  ←/→ Tab #{session['id'] if session else 'N/A'}[/dim]",
    )
