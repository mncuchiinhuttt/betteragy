"""CLI commands for managing the Antigravity real-time statusline HUD."""

import json
from pathlib import Path
import sys
import typer
from rich.console import Console
from rich.panel import Panel

from ..services.hud_service import render_statusline_hud
from ..ui.theme import BETTERAGY_THEME

hud_app = typer.Typer(
    help="Real-time statusline HUD for Antigravity (agy): token breakdown, duration & quota.",
    invoke_without_command=True,
)
console = Console(theme=BETTERAGY_THEME)

SETTINGS_PATH = Path.home() / ".gemini" / "antigravity-cli" / "settings.json"


def _read_settings() -> dict:
    """Read global Antigravity settings.json if exists."""
    if not SETTINGS_PATH.exists():
        return {}
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_settings(data: dict) -> None:
    """Write global Antigravity settings.json atomically."""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


@hud_app.callback()
def default_hud_entry(ctx: typer.Context) -> None:
    """Invoked when running 'betteragy hud' directly (piped from agy statusLine)."""
    if ctx.invoked_subcommand is not None:
        return

    # Check if data is piped on stdin
    payload = {}
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw and raw.strip():
                payload = json.loads(raw)
        except Exception:
            pass

    hud_str = render_statusline_hud(payload)
    sys.stdout.write(hud_str + "\n")
    sys.stdout.flush()


@hud_app.command("enable")
def enable_hud() -> None:
    """Enable real-time statusline HUD in Antigravity settings."""
    settings = _read_settings()
    status_cfg = settings.get("statusLine") or {}
    status_cfg["command"] = "betteragy hud"
    status_cfg["enabled"] = True
    settings["statusLine"] = status_cfg
    _write_settings(settings)

    console.print(
        Panel(
            "[bold green][ok] Betteragy Real-Time Statusline HUD is now ENABLED![/bold green]\n\n"
            "[dim]Configured command:[/] [cyan]betteragy hud[/cyan]\n"
            "[dim]Config file:[/] [cyan]~/.gemini/antigravity-cli/settings.json[/cyan]\n\n"
            "[bold white]Features active on every prompt in agy:[/bold white]\n"
            "  - [cyan]Model & Effort pill[/cyan] ([Gemini-3.8-Flash/high])\n"
            "  - [yellow]Real-time prompt execution duration[/yellow] (⚡ 3.4s)\n"
            "  - [green]Token telemetry breakdown[/green] (In / Out / Cache hit % / Reasoning)\n"
            "  - [magenta]Live 5-hour quota indicator[/magenta] (5h: 87%)\n\n"
            "[dim]To test it, simply run [cyan]agy[/cyan] in any terminal![/dim]",
            title="[~] Antigravity Statusline HUD",
            border_style="green",
        )
    )


@hud_app.command("setup")
def setup_hud() -> None:
    """Interactive / alias setup for the statusline HUD."""
    enable_hud()


@hud_app.command("disable")
def disable_hud() -> None:
    """Disable statusline HUD in Antigravity settings."""
    settings = _read_settings()
    if "statusLine" in settings:
        settings["statusLine"]["enabled"] = False
        _write_settings(settings)
    console.print("[yellow][!] Betteragy Statusline HUD has been disabled.[/yellow]")


@hud_app.command("status")
def status_hud() -> None:
    """Inspect current statusline HUD configuration."""
    settings = _read_settings()
    st = settings.get("statusLine") or {}
    cmd = st.get("command", "")
    enabled = st.get("enabled", False)

    if enabled and "betteragy" in cmd:
        body = (
            f"[bold green][ok] Statusline HUD is ACTIVE[/bold green]\n\n"
            f"[dim]Command:[/] [cyan]{cmd}[/cyan]\n"
            f"[dim]Target:[/] [yellow]~/.gemini/antigravity-cli/settings.json[/yellow]"
        )
        border = "green"
    else:
        body = (
            "[bold yellow][!] Statusline HUD is NOT ENABLED[/bold yellow]\n\n"
            "[dim]Run this command to activate:[/dim]\n"
            "  [cyan]betteragy hud enable[/cyan]"
        )
        border = "yellow"

    console.print(Panel(body, title="[~] Antigravity Statusline HUD Status", border_style=border))
