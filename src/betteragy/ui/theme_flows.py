"""Theme selector panel and interactive key navigation flows."""

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .key_listener import KEY_BACK, KEY_DOWN, KEY_ENTER, KEY_ESC, KEY_QUIT, KEY_UP
from .theme import DEFAULT_BOX, render_progress_bar
from .theme_catalog import ThemeDefinition
from .theme_manager import get_theme_manager


def render_theme_selector_panel(
    themes: list[ThemeDefinition],
    selected_idx: int,
    active_theme_id: str,
) -> Panel:
    """Render the theme selection panel with live sample previews."""
    th_mgr = get_theme_manager()
    active_th = th_mgr.get_active_theme()

    table = Table(box=DEFAULT_BOX, header_style=active_th.header_style, padding=(0, 1))
    table.add_column("Cursor", width=3, justify="center")
    table.add_column("#", style=active_th.dim_style, width=3, justify="right")
    table.add_column("Theme Name", min_width=18, no_wrap=True)
    table.add_column("Palette Style", style=active_th.dim_style, min_width=32, no_wrap=True)
    table.add_column("Quota Sample", justify="left", width=18, no_wrap=True)

    for i, item in enumerate(themes):
        is_sel = i == selected_idx
        is_active = item.id == active_theme_id
        cursor = f"[{active_th.cursor_style}]>[/{active_th.cursor_style}]" if is_sel else " "

        active_mark = f" [{item.quota_high}][*] Active[/{item.quota_high}]" if is_active else ""
        name_str = f"{item.name}{active_mark}"

        sample_bar = render_progress_bar(75, width=8, theme=item)
        row_style = active_th.sel_style if is_sel else None
        table.add_row(cursor, str(i + 1), name_str, item.description, sample_bar, style=row_style)

    instructions = Text(
        "\n[Up/Down] Navigate  |  [Enter] Apply Theme  |  [Esc/b] Back to Main Menu",
        style=active_th.dim_style,
    )
    return Panel(
        Group(table, instructions),
        title=f"[{active_th.title_style}]:: Color Theme Catalog ::[/{active_th.title_style}]",
        border_style=active_th.border_style,
        box=DEFAULT_BOX,
    )


def handle_theme_key(tui, key: str) -> bool:
    """Handle keyboard navigation on theme selector screen. Returns True to exit app."""
    th_mgr = get_theme_manager()
    themes = th_mgr.list_themes()
    total = len(themes)

    if key in (KEY_UP, KEY_DOWN):
        delta = -1 if key == KEY_UP else 1
        tui.theme_idx = (getattr(tui, "theme_idx", 0) + delta) % total
    elif key in (KEY_ESC, KEY_BACK):
        tui.current_screen = "main"
    elif key == KEY_QUIT:
        return True
    elif key == KEY_ENTER:
        if 0 <= tui.theme_idx < total:
            target_th = themes[tui.theme_idx]
            th_mgr.set_active_theme(target_th.id)
            from rich.console import Console
            tui.console = Console(theme=th_mgr.get_rich_theme())
            tui.status_message = f"[bold {target_th.quota_high}][ok] Theme switched to {target_th.name}[/bold {target_th.quota_high}]"
            tui.current_screen = "main"
    return False
