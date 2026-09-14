"""Hero KPI metric cards for usage and profile status."""

from typing import Optional
from rich.columns import Columns
from rich.panel import Panel

from ..core.models import AccountRecord, DeepUsageReport
from .theme import DEFAULT_BOX, format_cost, format_tokens


def render_kpi_cards(
    report: DeepUsageReport, active_account: Optional[AccountRecord] = None
) -> Columns:
    """Build high-impact KPI summary panels."""
    u = report.total_usage

    # Card 1: Active Profile
    acc_name = active_account.email if active_account else "None"
    tier_name = (active_account.tier_name or active_account.tier) if active_account else "Standard"
    p_profile = Panel(
        f"[bold white]{acc_name}[/bold white]\n[dim cyan]Tier: {tier_name}[/dim cyan]",
        title="[bold green]★ Active Account[/bold green]",
        box=DEFAULT_BOX,
        border_style="green",
    )

    # Card 2: Total Tokens
    p_tokens = Panel(
        f"[bold white]{format_tokens(u.total_tokens)}[/bold white]\n"
        f"[dim cyan]In: {format_tokens(u.input_tokens)}[/dim cyan] • "
        f"[dim green]Cache: {format_tokens(u.cache_read_tokens)}[/dim green] • "
        f"[dim magenta]Out: {format_tokens(u.output_tokens)}[/dim magenta]",
        title="[bold cyan]Total Tokens[/bold cyan]",
        box=DEFAULT_BOX,
        border_style="cyan",
    )

    # Card 3: Estimated Cost
    p_cost = Panel(
        f"[bold green]{format_cost(u.cost_usd)}[/bold green]\n"
        f"[dim yellow]Calls: {u.calls_count}[/dim yellow] • "
        f"[dim]Convos: {report.conversations_count}[/dim]",
        title="[bold yellow]Estimated Cost (USD)[/bold yellow]",
        box=DEFAULT_BOX,
        border_style="yellow",
    )

    return Columns([p_profile, p_tokens, p_cost], expand=True)
