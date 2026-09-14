"""Typer CLI application entry point for Betteragy."""

from typing import Optional
import typer
from rich.console import Console

from .commands.account_cmd import account_app
from .commands.quota_cmd import quota_command
from .commands.shell_cmd import shell_integration_command
from .commands.usage_cmd import usage_app
from .services.account_service import AccountService
from .services.quota_aggregator import QuotaAggregator
from .services.quota_service import QuotaService
from .services.usage_aggregator import UsageAggregator
from .ui.dashboard import run_live_dashboard
from .ui.theme import BETTERAGY_THEME

app = typer.Typer(
    name="betteragy",
    help="Rich CLI Switchboard & AI Token Analytics for Antigravity (agy)",
    rich_markup_mode="rich",
)

# Register command groups
app.add_typer(account_app, name="account")
app.add_typer(usage_app, name="usage")

# Register top-level commands
app.command("quota")(quota_command)
app.command("shell")(shell_integration_command)

console = Console(theme=BETTERAGY_THEME)
acc_svc = AccountService()
quota_svc = QuotaService()
quota_agg = QuotaAggregator(acc_svc, quota_svc)
usage_agg = UsageAggregator()


@app.command("dashboard")
def dashboard_view(
    interval: int = typer.Option(30, "--interval", "-i", help="Auto-refresh interval in seconds")
):
    """Launch full interactive live TUI dashboard."""
    def fetch_dashboard_state():
        active = acc_svc.get_active_account()
        q = quota_agg.fetch_single_account(active.email) if active else None
        rep = usage_agg.get_report(period="all")
        return rep, q, active

    run_live_dashboard(fetch_dashboard_state, refresh_interval=interval, console=console)


if __name__ == "__main__":
    app()
