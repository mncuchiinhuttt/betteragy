"""Usage command and subcommands: summary, models, and JSON exports."""

import json
import typer
from rich.console import Console

from ..services.account_service import AccountService
from ..services.usage_aggregator import UsageAggregator
from ..ui.cards import render_kpi_cards
from ..ui.tables import render_model_breakdown_table, render_top_conversations_table
from ..ui.theme import BETTERAGY_THEME

usage_app = typer.Typer(help="Token usage telemetry and estimated costs across conversations")
console = Console(theme=BETTERAGY_THEME)
acc_svc = AccountService()
usage_agg = UsageAggregator()


@usage_app.callback(invoke_without_command=True)
def usage_main(
    ctx: typer.Context,
    period: str = typer.Option("all", "--period", "-p", help="all, today, 24h, 7d, 30d"),
    refresh: bool = typer.Option(False, "--refresh", "-r", help="Force re-scan of databases"),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """View overall token usage and top conversations."""
    if ctx.invoked_subcommand is not None:
        return

    report = usage_agg.get_report(period=period, force_refresh=refresh)
    if as_json:
        console.print_json(json.dumps(report.model_dump()))
        return

    active = acc_svc.get_active_account()
    console.print(render_kpi_cards(report, active))
    if report.top_conversations:
        console.print(render_top_conversations_table(report))
    else:
        console.print("[dim]No conversations found for selected period.[/dim]")


@usage_app.command("models")
def usage_models(
    period: str = typer.Option("all", "--period", "-p", help="all, today, 24h, 7d, 30d"),
    refresh: bool = typer.Option(False, "--refresh", "-r", help="Force re-scan of databases"),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """View token consumption and costs broken down by model."""
    report = usage_agg.get_report(period=period, force_refresh=refresh)
    if as_json:
        console.print_json(json.dumps([m.model_dump() for m in report.models]))
        return

    if report.models:
        console.print(render_model_breakdown_table(report.models))
    else:
        console.print("[dim]No model telemetry recorded.[/dim]")
