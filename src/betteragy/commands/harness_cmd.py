"""CLI commands for managing agy reasoning harness."""

import typer
from rich.console import Console
from rich.panel import Panel

from betteragy.harness.harness_service import HarnessService

harness_app = typer.Typer(help="Manage agy deep thinking and verification harness.")
console = Console()


@harness_app.command("install")
def install_harness(
    profile: str = typer.Option(
        "strict",
        "--profile",
        "-p",
        help="Reasoning profile: 'strict' or 'balanced'.",
    ),
) -> None:
    """Install deep reasoning and verification rules into agy."""
    service = HarnessService()
    path = service.install(profile=profile)
    console.print(
        Panel(
            f"[bold green][ok] Deep reasoning harness installed successfully![/]\n"
            f"[dim]Profile:[/] [cyan]{profile}[/]\n"
            f"[dim]Rule File:[/] [yellow]{path}[/]\n"
            f"[dim]Global Rules:[/] [green]~/.gemini/GEMINI.md[/]\n\n"
            f"[bold white]All future 'agy' sessions will now enforce deep thinking & To-Do tracking.[/]",
            title="[~] Betteragy Harness",
            border_style="green",
        )
    )


@harness_app.command("status")
def harness_status() -> None:
    """Check whether agy reasoning harness is installed."""
    service = HarnessService()
    stat = service.status()
    if stat["installed"]:
        md_stat = "[bold green]Active[/]" if stat.get("gemini_md_active") else "[dim]Inactive[/]"
        console.print(
            Panel(
                f"[bold green][ok] Harness is active[/]\n"
                f"[dim]Profile:[/] [cyan]{stat['profile']}[/]\n"
                f"[dim]Location:[/] [yellow]{stat['path']}[/]\n"
                f"[dim]Global Rules (GEMINI.md):[/] {md_stat}\n"
                f"[dim]Size:[/] {stat['size_bytes']} bytes",
                title="[~] Betteragy Harness Status",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[bold yellow][!] Harness is not installed[/]\n"
                f"[dim]To activate, run:[/] [cyan]betteragy harness install[/]",
                title="[~] Betteragy Harness Status",
                border_style="yellow",
            )
        )


@harness_app.command("uninstall")
def uninstall_harness() -> None:
    """Remove deep reasoning rules from agy."""
    service = HarnessService()
    if service.uninstall():
        console.print("[bold yellow][ok] Removed agy reasoning harness.[/]")
    else:
        console.print("[dim]Harness was not installed.[/]")
