"""Live interactive TUI dashboard combining profile, quotas, and token KPIs."""

import time
from typing import Optional
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel

from .. import __version__
from ..core.models import AccountQuota, AccountRecord, DeepUsageReport
from .cards import render_kpi_cards
from .tables import render_quota_table, render_top_conversations_table
from .theme import DEFAULT_BOX


def build_dashboard_view(
    report: DeepUsageReport,
    quota: Optional[AccountQuota],
    active_account: Optional[AccountRecord],
) -> Group:
    """Compose the multi-section dashboard view."""
    elements = []

    # 1. Hero KPI Cards
    elements.append(render_kpi_cards(report, active_account))

    # 2. Live Quota Section
    if quota:
        elements.append(render_quota_table(quota))

    # 3. Top Conversations Section
    if report.top_conversations:
        elements.append(render_top_conversations_table(report))

    return Group(*elements)


def run_live_dashboard(
    fetch_data_callback, refresh_interval: int = 30, console: Optional[Console] = None
) -> None:
    """Run interactive live refreshing dashboard loop."""
    con = console or Console()
    con.print("[dim cyan]Starting Betteragy Live Dashboard (Ctrl+C to exit)...[/dim cyan]")

    with Live(console=con, auto_refresh=True, screen=True) as live:
        try:
            while True:
                report, quota, active_acc = fetch_data_callback()
                view = build_dashboard_view(report, quota, active_acc)
                footer = Panel(
                    f"[dim]Auto-refreshing every {refresh_interval}s | Press Ctrl+C to exit | Betteragy v{__version__}[/dim]",
                    box=DEFAULT_BOX,
                    style="dim",
                )
                live.update(Group(view, footer))
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            pass
