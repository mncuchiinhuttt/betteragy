"""Session visual panels and tab bar renderers for Betteragy."""

from typing import Any, Dict, List, Optional
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .theme import DEFAULT_BOX


def render_session_tab_bar(
    sessions: List[Dict[str, Any]],
    current_session_id: Optional[int] = None,
    max_visible: int = 4,
) -> RenderableType:
    """Render a horizontal tab bar of available task sessions with Left/Right navigation."""
    if not sessions:
        return Text("")

    cur_idx = 0
    if current_session_id is not None:
        for idx, s in enumerate(sessions):
            if s["id"] == current_session_id:
                cur_idx = idx
                break

    total_sess = len(sessions)
    if total_sess <= max_visible:
        visible_sessions = list(enumerate(sessions))
        show_left_more, show_right_more = False, False
    else:
        start = max(0, min(cur_idx - 1, total_sess - max_visible))
        end = start + max_visible
        visible_sessions = list(enumerate(sessions))[start:end]
        show_left_more, show_right_more = start > 0, end < total_sess

    bar = Text()
    bar.append("[< Left] " if show_left_more else "[<] ", style="cyan")
    for i, s in visible_sessions:
        is_sel = (s["id"] == current_session_id) or (current_session_id is None and i == 0)
        proj = s.get("project_name") or f"Session #{s['id']}"
        total = s.get("total_tasks", 0) or 0
        done = s.get("completed_tasks", 0) or 0
        pct = int((done / total) * 100) if total > 0 else 0
        act_star = "*" if s.get("is_active") else ""
        label = f" {act_star}#{s['id']} {proj} ({pct}%) "
        if is_sel:
            bar.append(f"[{label}]", style="bold cyan on #1e293b")
        else:
            bar.append(f" {label} ", style="dim white")
        bar.append(" ")
    bar.append("[Right >]" if show_right_more else "[>]", style="cyan")
    return bar


def render_sessions_table(sessions: List[Dict[str, Any]], active_id: Optional[int] = None) -> RenderableType:
    """Render a table listing all planning sessions with their progress."""
    if not sessions:
        return Panel(
            "[dim]No task sessions found. Run 'agy' or create a session to begin.[/]",
            title="[*] Betteragy Task Sessions",
            border_style="cyan",
        )

    table = Table(show_header=True, header_style="bold white", box=None, padding=(0, 1))
    table.add_column("Active", width=6, justify="center")
    table.add_column("ID", width=4, justify="right", style="dim")
    table.add_column("Goal", ratio=1)
    table.add_column("Project", width=14, style="cyan")
    table.add_column("Progress", width=12, justify="center")
    table.add_column("Tasks", width=8, justify="right")

    for s in sessions:
        is_act = bool(s.get("is_active")) or (active_id is not None and s["id"] == active_id)
        act_marker = Text("[*]", style="bold cyan") if is_act else Text("[ ]", style="dim")

        total = s.get("total_tasks", 0) or 0
        done = s.get("completed_tasks", 0) or 0
        pct = int((done / total) * 100) if total > 0 else 0
        prog_style = "bold green" if pct == 100 else ("yellow" if pct > 0 else "dim")
        prog_str = f"{pct}%" if total > 0 else "-"

        goal_text = Text(s.get("goal") or "Untitled Session")
        if is_act:
            goal_text.stylize("bold white")

        table.add_row(
            act_marker,
            str(s["id"]),
            goal_text,
            s.get("project_name") or "-",
            Text(prog_str, style=prog_style),
            f"{done}/{total}",
        )

    return Panel(
        table,
        title="[*] Betteragy Task Sessions",
        subtitle=f"[dim]{len(sessions)} session(s) found | Use 'betteragy tasks switch <id>' to switch[/]",
        border_style="cyan",
    )


def render_session_selector_panel(
    sessions: List[Dict[str, Any]],
    selected_idx: int,
    active_id: Optional[int] = None,
) -> Panel:
    """Render list of planning sessions navigable by arrow keys."""
    table = Table(box=DEFAULT_BOX, header_style="bold magenta", padding=(0, 1))
    table.add_column("Cursor", width=3, justify="center")
    table.add_column("ID", style="dim", width=4, justify="right")
    table.add_column("Goal", min_width=28)
    table.add_column("Project", style="cyan", width=14)
    table.add_column("Tasks", justify="center", width=8)
    table.add_column("Progress", justify="center", width=10)
    table.add_column("Status", justify="center", width=12)

    for i, s in enumerate(sessions):
        is_sel = i == selected_idx
        is_act = bool(s.get("is_active")) or (active_id is not None and s["id"] == active_id)
        cursor = "[bold cyan]>[/bold cyan]" if is_sel else " "
        status_str = "[bold cyan][*] Active[/]" if is_act else "[dim]Inactive[/]"

        total = s.get("total_tasks", 0) or 0
        done = s.get("completed_tasks", 0) or 0
        pct = int((done / total) * 100) if total > 0 else 0
        prog_style = "bold green" if pct == 100 else ("yellow" if pct > 0 else "dim")
        prog_str = f"{pct}%" if total > 0 else "-"

        row_style = "bold on #1e293b" if is_sel else None
        table.add_row(
            cursor,
            str(s["id"]),
            s.get("goal") or "Untitled",
            s.get("project_name") or "-",
            f"{done}/{total}",
            Text(prog_str, style=prog_style),
            status_str,
            style=row_style,
        )

    instructions = Text(
        "\n[Up/Down] Navigate  |  [Enter] Switch Session  |  [Esc/b] Back",
        style="dim cyan",
    )
    return Panel(
        Group(table, instructions),
        title="[bold cyan]:: Select Planning Session ::[/bold cyan]",
        border_style="cyan",
        box=DEFAULT_BOX,
    )
