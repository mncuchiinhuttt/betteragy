"""Screen layouts and interactive menu views for Betteragy TUI."""

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .. import __version__
from ..core.models import AccountRecord
from .theme import DEFAULT_BOX, format_status_badge
from .theme_manager import get_theme_manager

MAIN_MENU_ITEMS = [
    ("[1] Switch Account", "Switch active account for agy CLI and Keychain"),
    ("[2] Live AI Quotas", "Inspect remaining model % & reset countdowns"),
    ("[3] Token Usage", "All-time token consumption and estimated USD costs"),
    ("[4] Rotate Account", "Advance to next healthy account in rotation pool"),
    ("[5] Add Account", "Connect Google account via OAuth browser loopback"),
    ("[6] Remove Account", "Delete an account from your local switchboard pool"),
    ("[7] Tasks Planning", "Active agy task board, tab sessions & evidence"),
    ("[8] Thinking Harness", "Multi-angle reasoning rules and OMP invariants"),
    ("[9] Auto-Rotation Proxy", "Background MITM proxy daemon with 429 auto-swap"),
    ("[t] Color Themes", "Select palette (Warm, Emerald, Cyber, Dracula)"),
    ("[u] Check for Updates", "Check GitHub releases for latest version"),
    ("[x] Exit", "Return to shell prompt"),
]

ADD_ACCOUNT_METHODS = [
    ("[1] Browser Google OAuth", "Open system default browser to authenticate Google Account"),
    ("[2] Direct Refresh Token", "Paste an existing Google refresh_token in terminal prompt"),
]


def render_main_menu_panel(
    selected_idx: int,
    active_email: str,
    update_ver: str | None = None,
    proxy_active: bool = False,
) -> Panel:
    """Render the categorized main interactive menu with dynamic active theme styling."""
    th = get_theme_manager().get_active_theme()
    header = Text()
    header.append("Betteragy", style=th.title_style)
    header.append(f" v{__version__}", style=th.subtitle_style)
    if update_ver:
        header.append(f" [update: v{update_ver}]", style=f"bold {th.quota_high}")
    header.append(" -- Command Center\n", style="bold white")

    menu_table = Table(box=None, show_header=False, pad_edge=False, padding=(0, 1))
    menu_table.add_column("Cursor", width=3, justify="center")
    menu_table.add_column("Action", style="bold white", width=27)
    menu_table.add_column("Description", style=th.dim_style, min_width=35)

    for i, (title, desc) in enumerate(MAIN_MENU_ITEMS):
        is_sel = i == selected_idx
        cursor = f"[{th.cursor_style}]>[/{th.cursor_style}]" if is_sel else " "
        t_style = th.sel_style if is_sel else "bold white"
        d_style = th.dim_style if not is_sel else th.sel_style
        menu_table.add_row(cursor, Text(title, style=t_style), Text(desc, style=d_style))

    content = Group(header, menu_table)
    return Panel(
        content,
        title=f"[{th.title_style}]:: Command Menu ::[/{th.title_style}]",
        border_style=th.border_style,
        box=DEFAULT_BOX,
    )


def render_account_selector_panel(
    accounts: list[AccountRecord],
    selected_idx: int,
    active_email: str,
    title: str = "-- Select Account to Switch --",
    action_hint: str = "Switch to Selected Account",
) -> Panel:
    """Render list of accounts navigable by arrow keys."""
    th = get_theme_manager().get_active_theme()
    table = Table(box=DEFAULT_BOX, header_style=th.header_style, padding=(0, 1))
    table.add_column("Cursor", width=3, justify="center")
    table.add_column("#", style=th.dim_style, width=3, justify="right")
    table.add_column("Account / Email", min_width=26)
    table.add_column("Status", justify="center", width=16)
    table.add_column("Tier", style=th.secondary, width=18)

    for i, acc in enumerate(accounts):
        is_sel = i == selected_idx
        is_active = bool(active_email and acc.email.lower() == active_email.lower())
        badge = format_status_badge(is_active, False, acc.disabled, theme=th)
        tier_str = acc.tier_name or acc.tier or "Standard"

        cursor = f"[{th.cursor_style}]>[/{th.cursor_style}]" if is_sel else " "
        row_style = th.sel_style if is_sel else None
        table.add_row(cursor, str(i + 1), acc.email, badge, tier_str, style=row_style)

    instructions = Text(
        f"\n[Up/Down] Navigate  |  [Enter] {action_hint}  |  [Esc/b] Back",
        style=th.dim_style,
    )
    return Panel(
        Group(table, instructions),
        title=f"[{th.title_style}]{title}[/{th.title_style}]",
        border_style=th.border_style,
        box=DEFAULT_BOX,
    )


def render_add_account_panel(selected_idx: int) -> Panel:
    """Render the Add Account method selection panel."""
    th = get_theme_manager().get_active_theme()
    table = Table(box=None, show_header=False, pad_edge=False, padding=(0, 1))
    table.add_column("Cursor", width=3, justify="center")
    table.add_column("Method", style="bold white", width=28)
    table.add_column("Description", style=th.dim_style, min_width=45)

    for i, (title, desc) in enumerate(ADD_ACCOUNT_METHODS):
        is_sel = i == selected_idx
        cursor = f"[{th.cursor_style}]>[/{th.cursor_style}]" if is_sel else " "
        t_style = th.sel_style if is_sel else "bold white"
        d_style = th.dim_style if not is_sel else th.sel_style
        table.add_row(cursor, Text(title, style=t_style), Text(desc, style=d_style))

    instructions = Text("\n[Up/Down] Navigate  |  [Enter] Select Method  |  [Esc/b] Cancel", style=th.dim_style)
    return Panel(
        Group(table, instructions),
        title=f"[{th.title_style}]:: Connect New Google Account ::[/{th.title_style}]",
        border_style=th.border_style,
        box=DEFAULT_BOX,
    )


def render_oauth_waiting_panel(port: int = 19876) -> Panel:
    """Render waiting panel while browser authentication is in progress."""
    th = get_theme_manager().get_active_theme()
    content = Text()
    content.append("Default browser opened for Google Antigravity authentication.\n\n", style="bold white")
    content.append("Listening on: ", style=th.dim_style)
    content.append(f"http://127.0.0.1:{port}/callback\n\n", style=f"bold {th.quota_high}")
    content.append("Please complete login and consent in your browser window...\n", style=th.primary)
    content.append("\n[Esc/b] Cancel authentication and return to menu", style=th.dim_style)
    return Panel(
        content,
        title=f"[{th.title_style}]:: Google OAuth in Progress ::[/{th.title_style}]",
        border_style=th.border_style,
        box=DEFAULT_BOX,
    )


def render_footer_hints(screen_name: str = "main") -> Panel:
    """Render contextual keybinding hints at the bottom of the screen."""
    th = get_theme_manager().get_active_theme()
    if screen_name == "main":
        hints = f"[{th.primary}]↑/↓/1-9[/{th.primary}] Navigate  |  [{th.quota_high}]Enter[/{th.quota_high}] Select  |  [{th.accent}]f[/{th.accent}] Fireworks  |  [{th.secondary}]p[/{th.secondary}] Proxy  |  [{th.quota_low}]q[/{th.quota_low}] Exit"
    elif screen_name == "oauth":
        hints = f"[{th.quota_low}]Esc/b[/{th.quota_low}] Cancel Login  |  [{th.quota_low}]q[/{th.quota_low}] Exit"
    elif screen_name == "tasks":
        hints = f"[{th.primary}]Esc/b[/{th.primary}] Menu  |  [{th.primary}]Left/Right[/{th.primary}] Switch Tab  |  [{th.quota_high}]Enter[/{th.quota_high}] Set Active  |  [{th.secondary}]r[/{th.secondary}] Refresh  |  [{th.quota_low}]q[/{th.quota_low}] Exit"
    elif screen_name == "session_selector":
        hints = f"[{th.primary}]Up/Down[/{th.primary}] Navigate  |  [{th.quota_high}]Enter[/{th.quota_high}] Switch  |  [{th.quota_low}]Esc/b[/{th.quota_low}] Back"
    elif screen_name == "theme":
        hints = f"[{th.primary}]Up/Down[/{th.primary}] Navigate  |  [{th.quota_high}]Enter[/{th.quota_high}] Apply Theme  |  [{th.quota_low}]Esc/b[/{th.quota_low}] Back"
    elif screen_name == "proxy":
        hints = f"[{th.primary}]p[/{th.primary}] Toggle Proxy  |  [{th.secondary}]r[/{th.secondary}] Refresh  |  [{th.quota_low}]Esc/b[/{th.quota_low}] Back  |  [{th.quota_low}]q[/{th.quota_low}] Exit"
    else:
        hints = f"[{th.primary}]Esc/b[/{th.primary}] Back to Menu  |  [{th.quota_low}]q[/{th.quota_low}] Exit"

    return Panel(Align.center(Text.from_markup(hints)), box=DEFAULT_BOX, style=th.dim_style)
