"""Agent launcher and shell alias helper for high reasoning agy sessions."""

import os
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

agent_app = typer.Typer(help="Launch agy with maximum reasoning effort and setup shell alias.")
console = Console()


def _get_agent_env() -> dict:
    env = os.environ.copy()
    from ..proxy.daemon import is_proxy_running
    from ..proxy.server import DEFAULT_PROXY_HOST, DEFAULT_PROXY_PORT
    from ..services.cert_service import CertService
    if is_proxy_running():
        ca_file = CertService().get_ca_cert_path()
        env["HTTPS_PROXY"] = f"http://{DEFAULT_PROXY_HOST}:{DEFAULT_PROXY_PORT}"
        env["SSL_CERT_FILE"] = str(ca_file)
    return env


@agent_app.callback(invoke_without_command=True)
def default_agent(
    ctx: typer.Context,
    skip_permissions: bool = typer.Option(
        True,
        "--dangerously-skip-permissions",
        "-y",
        help="Auto-approve all tool permission requests without prompting",
    ),
) -> None:
    """Launch agy with maximum reasoning effort (--effort high)."""
    if ctx.invoked_subcommand is None:
        cmd = ["agy", "--effort", "high"]
        if skip_permissions:
            cmd.append("--dangerously-skip-permissions")
        try:
            subprocess.run(cmd, env=_get_agent_env())
        except FileNotFoundError:
            console.print("[bold red][!] 'agy' binary not found in PATH.[/]")


@agent_app.command("run")
def run_agent(
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Initial prompt to send to agy"),
    effort: str = typer.Option("high", "--effort", "-e", help="Reasoning effort (low|medium|high)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
    skip_permissions: bool = typer.Option(
        True,
        "--dangerously-skip-permissions",
        "-y",
        help="Auto-approve all tool permission requests without prompting",
    ),
) -> None:
    """Run agy with custom prompt, reasoning effort, or model."""
    cmd = ["agy", "--effort", effort]
    if skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    if model:
        cmd.extend(["--model", model])
    if prompt:
        cmd.extend(["-p", prompt])

    try:
        subprocess.run(cmd, env=_get_agent_env())
    except FileNotFoundError:
        console.print("[bold red][!] 'agy' binary not found in PATH.[/]")


@agent_app.command("setup-alias")
def setup_alias() -> None:
    """Configure 'alias agy=\"agy --effort high --dangerously-skip-permissions\"' in shell profile."""
    zshrc = Path.home() / ".zshrc"
    bashrc = Path.home() / ".bashrc"
    target = zshrc if zshrc.exists() else bashrc

    alias_line = 'alias agy="agy --effort high --dangerously-skip-permissions"\n'

    if target.exists():
        content = target.read_text(encoding="utf-8")
        if 'alias agy=' in content or 'agy()' in content:
            console.print(f"[yellow][!] 'agy' alias/wrapper already exists in {target}.[/]")
            return

    with open(target, "a", encoding="utf-8") as f:
        f.write(f"\n# Betteragy deep thinking alias\n{alias_line}")

    console.print(
        Panel(
            f"[bold green][ok] Configured alias in {target}![/]\n"
            f"[dim]Run:[/] [cyan]source {target}[/]\n\n"
            f"[bold white]Now, typing 'agy' runs with '--effort high --dangerously-skip-permissions'![/]",
            title="[~] Betteragy Shell Alias",
            border_style="green",
        )
    )
