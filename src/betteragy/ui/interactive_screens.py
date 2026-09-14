"""Screen layouts and interactive menu views for Betteragy TUI."""

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..core.models import AccountRecord
from .theme import DEFAULT_BOX, format_status_badge

MAIN_MENU_ITEMS = [
    ("🔄 Switch Account", "Switch active account session for agy CLI and Keychain"),
    ("📊 Live AI Quotas", "View real-time model quota percentages and reset countdowns"),
    ("📈 Token Usage & Costs", "View all-time token consumption and estimated USD costs"),
    ("🎲 Rotate Account", "Advance to next healthy account using configured strategy"),
    ("⏳ Set Cooldown", "Mark current account rate-limited for 4h and auto-rotate"),
    ("➕ Add Account", "Connect a new Google account via OAuth or direct token"),
    ("🗑️  Remove Account", "Delete an account from your local switchboard pool"),
    ("🐚 Shell Integration", "View bash/zsh wrapper function and aliases for agy"),
    ("🚪 Exit", "Exit Betteragy and return to shell"),
]


def render_main_menu_panel(selected_idx: int, active_email: str) -> Panel:
    """Render the main interactive menu with cursor selection."""
    header = Text()
    header.append("Betteragy", style="bold cyan")
    header.append(" — Interactive Switchboard & Token Analytics\n", style="bold white")
    header.append("Active Account: ", style="dim")
    header.append(f"{active_email or 'None'}\n", style="bold green")

    menu_table = Table(box=None, show_header=False, pad_edge=False, padding=(0, 1))
    menu_table.add_column("Cursor", width=3, justify="center")
    menu_table.add_column("Action", style="bold white", width=24)
    menu_table.add_column("Description", style="dim", min_width=45)

    for i, (title, desc) in enumerate(MAIN_MENU_ITEMS):
        is_sel = i == selected_idx
        if is_sel:
            cursor = "[bold cyan]▶[/bold cyan]"
            t_style = "bold cyan on #1e293b"
            d_style = "white on #1e293b"
        else:
            cursor = " "
            t_style = "bold white"
            d_style = "dim"

        menu_table.add_row(cursor, Text(title, style=t_style), Text(desc, style=d_style))

    content = Group(header, menu_table)
    return Panel(
        content,
        title="[bold magenta]⚡ Main Menu[/bold magenta]",
        border_style="cyan",
        box=DEFAULT_BOX,
    )


def render_account_selector_panel(
    accounts: list[AccountRecord], selected_idx: int, active_email: str
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

        cursor = "[bold cyan]▶[/bold cyan]" if is_sel else " "
        row_style = "bold on #1e293b" if is_sel else None
        table.add_row(cursor, str(i + 1), acc.email, badge, tier_str, style=row_style)

    instructions = Text(
        "\n[↑/↓] Navigate  •  [Enter] Switch to Selected Account  •  [Esc/b] Back",
        style="dim cyan",
    )
    return Panel(
        Group(table, instructions),
        title="[bold cyan]🔄 Select Account to Switch[/bold cyan]",
        border_style="cyan",
        box=DEFAULT_BOX,
    )


def render_footer_hints(screen_name: str = "main") -> Panel:
    """Render contextual keybinding hints at the bottom of the screen."""
    if screen_name == "main":
        hints = "[bold cyan]↑/k[/bold cyan] Up  •  [bold cyan]↓/j[/bold cyan] Down  •  [bold green]Enter[/bold green] Select  •  [bold red]q[/bold red] Exit"
    else:
        hints = "[bold cyan]Esc/b[/bold cyan] Back to Menu  •  [bold red]q[/bold red] Exit"

    return Panel(
        Align.center(Text.from_markup(hints)),
        box=DEFAULT_BOX,
        style="dim",
    )
