"""CLI commands to start, stop, and inspect the Betteragy local proxy daemon."""

import asyncio
import os
import typer
from rich.console import Console
from rich.panel import Panel

from ..proxy.daemon import (
    LOG_FILE,
    PID_FILE,
    get_proxy_pid,
    is_healthy,
    is_proxy_running,
    start_proxy_daemon,
    stop_proxy_daemon,
)
from ..proxy.server import DEFAULT_PROXY_HOST, DEFAULT_PROXY_PORT, BetteragyProxyServer
from ..services.cert_service import DEFAULT_CERTS_DIR
from ..ui.theme import BETTERAGY_THEME

proxy_app = typer.Typer(help="Manage local zero-restart proxy with auto-rotation on quota exhaustion.")
console = Console(theme=BETTERAGY_THEME)


@proxy_app.command("start")
def start_proxy(
    host: str = typer.Option(DEFAULT_PROXY_HOST, "--host", "-h", help="Host interface to bind"),
    port: int = typer.Option(DEFAULT_PROXY_PORT, "--port", "-p", help="Port number"),
    foreground: bool = typer.Option(False, "--foreground", "-f", help="Run in foreground"),
) -> None:
    """Start local proxy daemon for zero-restart switching & auto-rotation."""
    if foreground:
        server = BetteragyProxyServer(host=host, port=port)
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
        try:
            asyncio.run(server.serve_forever())
        finally:
            PID_FILE.unlink(missing_ok=True)
        return

    success, pid, msg = start_proxy_daemon(host, port)
    ca_path = DEFAULT_CERTS_DIR / "ca.crt"

    if success:
        console.print(
            Panel(
                f"[bold green][ok] Betteragy proxy started successfully![/bold green]\n\n"
                f"[dim]PID:[/] [cyan]{pid}[/cyan]  |  [dim]Listening:[/] [cyan]http://{host}:{port}[/cyan]\n"
                f"[dim]Auto-Rotation:[/] [bold yellow]Enabled (Catches HTTP 429 quota exhaustion)[/bold yellow]\n"
                f"[dim]Zero-Restart Switching:[/] [bold green]Active[/bold green]\n\n"
                f"[bold white]To run agy through the proxy:[/bold white]\n"
                f"  [cyan]export HTTPS_PROXY=http://{host}:{port}[/cyan]\n"
                f"  [cyan]export SSL_CERT_FILE={ca_path}[/cyan]\n"
                f"  [cyan]agy[/cyan]",
                title="[~] Betteragy Transparent Proxy",
                border_style="green",
            )
        )
    else:
        console.print(f"[yellow][!] {msg}. Check {LOG_FILE}[/yellow]")


@proxy_app.command("stop")
def stop_proxy() -> None:
    """Stop running proxy daemon."""
    stopped = stop_proxy_daemon()
    if stopped:
        console.print("[bold green][ok] Betteragy proxy daemon stopped.[/bold green]")
    else:
        console.print("[yellow][!] Betteragy proxy is not running.[/yellow]")


@proxy_app.command("status")
def status_proxy(
    host: str = typer.Option(DEFAULT_PROXY_HOST, "--host", "-h"),
    port: int = typer.Option(DEFAULT_PROXY_PORT, "--port", "-p"),
) -> None:
    """Inspect proxy daemon running status and active account."""
    pid = get_proxy_pid()
    healthy = is_healthy(host, port)
    ca_path = DEFAULT_CERTS_DIR / "ca.crt"

    if pid and healthy:
        body = (
            f"[bold green][ok] Proxy Daemon is ACTIVE[/bold green]\n\n"
            f"[dim]PID:[/] [cyan]{pid}[/cyan]\n"
            f"[dim]Endpoint:[/] [cyan]http://{host}:{port}[/cyan]\n"
            f"[dim]SSL CA Cert:[/] [yellow]{ca_path}[/yellow]\n"
            f"[dim]Auto-Rotation:[/] [bold green]Enabled (auto-swaps token on 429)[/bold green]\n\n"
            f"[bold white]Environment variables for agy:[/bold white]\n"
            f"  [cyan]HTTPS_PROXY=http://{host}:{port}[/cyan]\n"
            f"  [cyan]SSL_CERT_FILE={ca_path}[/cyan]"
        )
        border = "green"
    else:
        body = (
            "[bold yellow][!] Proxy Daemon is STOPPED[/bold yellow]\n\n"
            "[dim]To start the zero-restart proxy with auto-rotation:[/dim]\n"
            "  [cyan]betteragy proxy start[/cyan]"
        )
        border = "yellow"

    console.print(Panel(body, title="[~] Betteragy Proxy Status", border_style=border))


@proxy_app.command("run", hidden=True)
def run_proxy(
    host: str = typer.Option(DEFAULT_PROXY_HOST, "--host", "-h"),
    port: int = typer.Option(DEFAULT_PROXY_PORT, "--port", "-p"),
) -> None:
    """Internal entrypoint for background daemon."""
    server = BetteragyProxyServer(host=host, port=port)
    asyncio.run(server.serve_forever())
