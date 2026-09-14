"""Quota command: live AI model quotas and watch mode."""

import json
import time
from typing import Optional
import typer
from rich.console import Console
from rich.live import Live

from ..services.account_service import AccountService
from ..services.quota_aggregator import QuotaAggregator
from ..services.quota_service import QuotaService
from ..ui.tables import render_multi_quota_matrix, render_quota_table
from ..ui.theme import BETTERAGY_THEME

console = Console(theme=BETTERAGY_THEME)
acc_svc = AccountService()
quota_svc = QuotaService()
quota_agg = QuotaAggregator(acc_svc, quota_svc)


def quota_command(
    account: Optional[str] = typer.Option(None, "--account", "-a", help="Specific account index or email"),
    all_accounts: bool = typer.Option(False, "--all", help="Show matrix across all accounts"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Live auto-refresh mode"),
    interval: int = typer.Option(30, "--interval", "-i", help="Watch refresh interval in seconds"),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """View live AI model quotas and reset countdown timers."""
    if watch:
        console.print(f"[dim cyan]Watching live quotas (refreshing every {interval}s, Ctrl+C to exit)...[/dim cyan]")
        with Live(console=console, auto_refresh=True) as live:
            try:
                while True:
                    if all_accounts:
                        quotas = quota_agg.fetch_all_accounts()
                        live.update(render_multi_quota_matrix(quotas))
                    else:
                        target = acc_svc.find_account(account) if account else acc_svc.get_active_account()
                        if not target:
                            live.update("[yellow]No account available to check quota.[/yellow]")
                        else:
                            q = quota_agg.fetch_single_account(target.email)
                            live.update(render_quota_table(q))
                    time.sleep(interval)
            except KeyboardInterrupt:
                return

    if all_accounts:
        quotas = quota_agg.fetch_all_accounts()
        if as_json:
            console.print_json(json.dumps([q.model_dump() for q in quotas]))
            return
        console.print(render_multi_quota_matrix(quotas))
        return

    target = acc_svc.find_account(account) if account else acc_svc.get_active_account()
    if not target:
        console.print("[yellow]No account available to check quota.[/yellow]")
        raise typer.Exit(1)

    quota = quota_agg.fetch_single_account(target.email)
    if as_json:
        console.print_json(json.dumps(quota.model_dump()))
        return
    console.print(render_quota_table(quota))
