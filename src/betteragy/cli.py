import sys
from typing import Optional
import typer
from rich.console import Console

from . import __version__
from .commands.account_cmd import account_app
from .commands.agent_cmd import agent_app
from .commands.harness_cmd import harness_app
from .commands.hud_cmd import hud_app
from .commands.mcp_cmd import mcp_app
from .commands.proxy_cmd import proxy_app
from .commands.quota_cmd import quota_command
from .commands.shell_cmd import shell_integration_command
from .commands.tasks_cmd import tasks_app
from .commands.usage_cmd import usage_app
from .services.account_service import AccountService
from .services.quota_aggregator import QuotaAggregator
from .services.quota_service import QuotaService
from .services.usage_aggregator import UsageAggregator
from .ui.dashboard import run_live_dashboard
from .ui.interactive_tui import run_interactive_tui
from .ui.theme import BETTERAGY_THEME

app = typer.Typer(
    name="betteragy",
    help="Rich CLI Switchboard & AI Token Analytics for Antigravity (agy)",
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    """Print version and exit eagerly."""
    if value:
        console.print(
            f"[bold cyan]betteragy[/bold cyan] version [bold green]{__version__}[/bold green] "
            f"[dim]by[/dim] [bold cyan]@mncuchiinhuttt[/bold cyan] [dim](Long Minh Vo)[/dim]"
        )
        raise typer.Exit()

# Register command groups
app.add_typer(account_app, name="account")
app.add_typer(usage_app, name="usage")
app.add_typer(harness_app, name="harness")
app.add_typer(mcp_app, name="mcp")
app.add_typer(tasks_app, name="tasks")
app.add_typer(agent_app, name="agent")
app.add_typer(proxy_app, name="proxy")
app.add_typer(hud_app, name="hud")
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


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        "-v",
        help="Show betteragy version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Launch interactive TUI menu when invoked without subcommands."""
    if ctx.invoked_subcommand is None:
        from .services.onboarding_service import OnboardingService
        from .ui.onboarding_wizard import run_onboarding_wizard

        onboard_svc = OnboardingService()
        if onboard_svc.is_onboarding_needed():
            run_onboarding_wizard(onboard_svc, interactive=sys.stdin.isatty())

        if sys.stdin.isatty():
            run_interactive_tui()
        else:
            console.print(ctx.get_help())


@app.command("version")
def version_command():
    """Display version and build information."""
    console.print(
        f"[bold cyan]betteragy[/bold cyan] version [bold green]{__version__}[/bold green] "
        f"[dim]by[/dim] [bold cyan]@mncuchiinhuttt[/bold cyan] [dim](Long Minh Vo)[/dim]"
    )


@app.command("update")
@app.command("check-update")
def update_command():
    """Check for updates from GitHub and print upgrade instructions."""
    from rich.panel import Panel
    from .services.update_service import UpdateService

    console.print("[dim]Checking for Betteragy updates from GitHub...[/dim]")
    info = UpdateService().check_for_updates(force=True)
    if info and info.is_newer:
        console.print(
            Panel(
                f"[bold yellow][~] New version available: v{info.latest_version}[/bold yellow] (Current: v{info.current_version})\n\n"
                f"Release URL: [cyan]{info.release_url}[/cyan]\n\n"
                f"[bold white]To upgrade, run:[/bold white]\n"
                f"  [green]pip install -U git+https://github.com/mncuchiinhuttt/betteragy.git[/green]",
                title="[~] Betteragy Update Available",
                border_style="yellow",
            )
        )
    else:
        cur = info.current_version if info else __version__
        console.print(f"[bold green][ok] Betteragy is up to date (v{cur})[/bold green]")


@app.command("menu")
@app.command("ui")
def menu_command():
    """Launch interactive arrow-key TUI menu."""
    run_interactive_tui()


@app.command("setup")
@app.command("onboard")
def setup_command(
    force: bool = typer.Option(False, "--force", "-f", help="Force rerun onboarding wizard even if already set up"),
    reset: bool = typer.Option(False, "--reset", "-r", help="Reset onboarding state to simulate first-run experience"),
):
    """Run interactive first-time setup and onboarding wizard."""
    from .services.onboarding_service import OnboardingService
    from .ui.onboarding_wizard import run_onboarding_wizard

    svc = OnboardingService()
    if reset:
        svc.reset()
        console.print("[bold green][ok] Onboarding state reset. Next run will trigger setup.[/bold green]")
        return
    if force:
        svc.reset()
    run_onboarding_wizard(svc, interactive=sys.stdin.isatty())


if __name__ == "__main__":
    app()

