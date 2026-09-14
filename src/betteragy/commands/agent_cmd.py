"""Agent launcher and shell alias helper for high reasoning agy sessions."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

agent_app = typer.Typer(help="Launch agy with maximum reasoning effort and setup shell alias.")
console = Console()


@agent_app.callback(invoke_without_command=True)
def default_agent(ctx: typer.Context) -> None:
    """Launch agy with maximum reasoning effort (--effort high)."""
    if ctx.invoked_subcommand is None:
        cmd = ["agy", "--effort", "high"]
        try:
            subprocess.run(cmd)
        except FileNotFoundError:
            console.print("[bold red][!] 'agy' binary not found in PATH.[/]")


@agent_app.command("run")
def run_agent(
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Initial prompt to send to agy"),
    effort: str = typer.Option("high", "--effort", "-e", help="Reasoning effort (low|medium|high)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
) -> None:
    """Run agy with custom prompt, reasoning effort, or model."""
    cmd = ["agy", "--effort", effort]
    if model:
        cmd.extend(["--model", model])
    if prompt:
        cmd.extend(["-p", prompt])

    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        console.print("[bold red][!] 'agy' binary not found in PATH.[/]")



@agent_app.command("setup-alias")
def setup_alias() -> None:
    """Configure 'alias agy=\"agy --effort high\"' in ~/.zshrc or ~/.bashrc."""
    zshrc = Path.home() / ".zshrc"
    bashrc = Path.home() / ".bashrc"
    target = zshrc if zshrc.exists() else bashrc

    alias_line = 'alias agy="agy --effort high"\n'

    if target.exists():
        content = target.read_text(encoding="utf-8")
        if 'alias agy=' in content:
            console.print(f"[yellow][!] 'agy' alias already exists in {target}.[/]")
            return

    with open(target, "a", encoding="utf-8") as f:
        f.write(f"\n# Betteragy deep thinking alias\n{alias_line}")

    console.print(
        Panel(
            f"[bold green][ok] Configured alias in {target}![/]\n"
            f"[dim]Run:[/] [cyan]source {target}[/]\n\n"
            f"[bold white]Now, every time you type 'agy', it will automatically run with '--effort high'![/]",
            title="[~] Betteragy Shell Alias",
            border_style="green",
        )
    )
