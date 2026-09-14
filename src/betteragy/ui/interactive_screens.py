"""Screen layouts and interactive menu views for Betteragy TUI."""

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..core.models import AccountRecord
from .theme import DEFAULT_BOX, format_status_badge

MAIN_MENU_ITEMS = [
    ("[~] Switch Account", "Switch active account session for agy CLI and Keychain"),
    ("[#] Live AI Quotas", "View real-time model quota percentages and reset countdowns"),
    ("[$] Token Usage & Costs", "View all-time token consumption and estimated USD costs"),
    ("[*] Rotate Account", "Advance to next healthy account using configured strategy"),
    ("[!] Set Cooldown", "Mark current account rate-limited for 4h and auto-rotate"),
    ("[+] Add Account", "Connect a new Google account via OAuth or direct token"),
    ("[-] Remove Account", "Delete an account from your local switchboard pool"),
    ("[>] Shell Integration", "View bash/zsh wrapper function and aliases for agy"),
    ("[x] Exit", "Exit Betteragy and return to shell"),
]

ADD_ACCOUNT_METHODS = [
    ("[1] Browser Google OAuth", "Open system default browser to authenticate Google Account"),
    ("[2] Direct Refresh Token", "Paste an existing Google refresh_token in terminal prompt"),
]


def render_main_menu_panel(selected_idx: int, active_email: str) -> Panel:
    """Render the main interactive menu with cursor selection."""
    header = Text()
    header.append("Betteragy", style="bold cyan")
    header.append(" -- Interactive Switchboard & Token Analytics\n", style="bold white")
    header.append("Active Account: ", style="dim")
    header.append(f"{active_email or 'None'}\n", style="bold green")

    menu_table = Table(box=None, show_header=False, pad_edge=False, padding=(0, 1))
    menu_table.add_column("Cursor", width=3, justify="center")
    menu_table.add_column("Action", style="bold white", width=26)
    menu_table.add_column("Description", style="dim", min_width=45)

    for i, (title, desc) in enumerate(MAIN_MENU_ITEMS):
        is_sel = i == selected_idx
        cursor = "[bold cyan]>[/bold cyan]" if is_sel else " "
        t_style = "bold cyan on #1e293b" if is_sel else "bold white"
        d_style = "white on #1e293b" if is_sel else "dim"
        menu_table.add_row(cursor, Text(title, style=t_style), Text(desc, style=d_style))

    content = Group(header, menu_table)
    return Panel(
        content,
        title="[bold magenta]:: Main Menu ::[/bold magenta]",
        border_style="cyan",
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
    table = Table(box=DEFAULT_BOX, header_style="bold magenta", padding=(0, 1))
    table.add_column("Cursor", width=3, justify="center")
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("Account / Email", min_width=26)
    table.add_column("Status", justify="center", width=16)
    table.add_column("Tier", style="cyan", width=18)

    for i, acc in enumerate(accounts):
        is_sel = i == selected_idx
        is_active = bool(active_email and acc.email.lower() == active_email.lower())
        badge = format_status_badge(is_active, False, acc.disabled)
        tier_str = acc.tier_name or acc.tier or "Standard"

        cursor = "[bold cyan]>[/bold cyan]" if is_sel else " "
        row_style = "bold on #1e293b" if is_sel else None
        table.add_row(cursor, str(i + 1), acc.email, badge, tier_str, style=row_style)

    instructions = Text(
        f"\n[Up/Down] Navigate  |  [Enter] {action_hint}  |  [Esc/b] Back",
        style="dim cyan",
    )
    return Panel(
        Group(table, instructions),
        title=f"[bold cyan]{title}[/bold cyan]",
        border_style="cyan",
        box=DEFAULT_BOX,
    )


def render_add_account_panel(selected_idx: int) -> Panel:
    """Render the Add Account method selection panel."""
    table = Table(box=None, show_header=False, pad_edge=False, padding=(0, 1))
    table.add_column("Cursor", width=3, justify="center")
    table.add_column("Method", style="bold white", width=28)
    table.add_column("Description", style="dim", min_width=45)

    for i, (title, desc) in enumerate(ADD_ACCOUNT_METHODS):
        is_sel = i == selected_idx
        cursor = "[bold cyan]>[/bold cyan]" if is_sel else " "
        t_style = "bold cyan on #1e293b" if is_sel else "bold white"
        d_style = "white on #1e293b" if is_sel else "dim"
        table.add_row(cursor, Text(title, style=t_style), Text(desc, style=d_style))

    instructions = Text("\n[Up/Down] Navigate  |  [Enter] Select Method  |  [Esc/b] Cancel", style="dim cyan")
    return Panel(
        Group(table, instructions),
        title="[bold cyan]:: Connect New Google Account ::[/bold cyan]",
        border_style="cyan",
        box=DEFAULT_BOX,
    )


def render_oauth_waiting_panel(port: int = 19876) -> Panel:
    """Render waiting panel while browser authentication is in progress."""
    content = Text()
    content.append("Default browser opened for Google Antigravity authentication.\n\n", style="bold white")
    content.append("Listening on: ", style="dim")
    content.append(f"http://127.0.0.1:{port}/callback\n\n", style="bold green")
    content.append("Please complete login and consent in your browser window...\n", style="cyan")
    content.append("\n[Esc/b] Cancel authentication and return to menu", style="dim")
    return Panel(
        content,
        title="[bold cyan]:: Google OAuth in Progress ::[/bold cyan]",
        border_style="cyan",
        box=DEFAULT_BOX,
    )


def render_footer_hints(screen_name: str = "main") -> Panel:
    """Render contextual keybinding hints at the bottom of the screen."""
    if screen_name == "main":
        hints = "[bold cyan]Up/k[/bold cyan] Up  |  [bold cyan]Down/j[/bold cyan] Down  |  [bold green]Enter[/bold green] Select  |  [bold red]q[/bold red] Exit"
    elif screen_name == "oauth":
        hints = "[bold red]Esc/b[/bold red] Cancel Login  |  [bold red]q[/bold red] Exit"
    else:
        hints = "[bold cyan]Esc/b[/bold cyan] Back to Menu  |  [bold red]q[/bold red] Exit"

    return Panel(Align.center(Text.from_markup(hints)), box=DEFAULT_BOX, style="dim")
