"""UI panel and event handlers for the Auto-Rotation Local Proxy screen."""

from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from ..core.constants import CONFIG_DIR
from ..proxy.daemon import (
    get_proxy_pid,
    is_healthy,
    is_proxy_running,
    start_proxy_daemon,
    stop_proxy_daemon,
)
from ..proxy.server import DEFAULT_PROXY_HOST, DEFAULT_PROXY_PORT
from ..services.cert_service import DEFAULT_CERTS_DIR
from .key_listener import KEY_BACK, KEY_ESC, KEY_QUIT, KEY_REFRESH
from .theme import DEFAULT_BOX


def render_proxy_panel(tui) -> Panel:
    """Render status and control panel for the local auto-rotation proxy."""
    pid = get_proxy_pid()
    healthy = is_healthy(DEFAULT_PROXY_HOST, DEFAULT_PROXY_PORT)
    active_acc = tui.acc_svc.get_active_account()
    active_email = active_acc.email if active_acc else "None"
    from ..services.cert_service import CertService
    ca_file = CertService().get_ca_cert_path()

    text = Text()
    text.append("Betteragy Transparent Local Proxy", style="bold cyan")
    text.append(" -- Auto-Rotation & Live Account Switching\n\n", style="bold white")

    if pid and healthy:
        text.append("Status:         ", style="dim")
        text.append(f"[ok] ACTIVE (PID: {pid})\n", style="bold green")
        text.append("Endpoint:       ", style="dim")
        text.append(f"http://{DEFAULT_PROXY_HOST}:{DEFAULT_PROXY_PORT}\n", style="cyan")
        text.append("Forwarding To:  ", style="dim")
        text.append(f"{active_email} (Bearer token dynamically injected)\n", style="bold white")
        text.append("Auto-Rotation:  ", style="dim")
        text.append("[ok] ENABLED (Transparent 429 Retry + 4h Cooldown)\n", style="bold green")
        text.append("Auto-Config:    ", style="dim")
        text.append("[ok] INSTALLED (Shell auto-routes agy while proxy is active)\n", style="bold green")
        text.append("Root CA Cert:   ", style="dim")
        text.append(f"{ca_file}\n\n", style="yellow")

        text.append("Environment Configuration (Auto-managed):\n", style="bold white")
        text.append(f"  HTTPS_PROXY=http://{DEFAULT_PROXY_HOST}:{DEFAULT_PROXY_PORT}\n", style="cyan")
        text.append(f"  SSL_CERT_FILE={ca_file}\n", style="cyan")
        text.append("  (Zero manual export needed: simply run 'agy' in your terminal)\n\n", style="dim")
        border = "green"
    else:
        text.append("Status:         ", style="dim")
        text.append("[!] STOPPED\n\n", style="bold yellow")
        text.append("Features when active:\n", style="bold white")
        text.append("  [*] Auto-Rotation: ", style="bold cyan")
        text.append("When current account hits 429 rate-limits, proxy auto-swaps to next healthy account.\n", style="white")
        text.append("  [*] Zero-Restart Switching: ", style="bold cyan")
        text.append("Switch accounts in Betteragy without restarting any running agy sessions.\n", style="white")
        text.append("  [*] Zero Manual Config: ", style="bold cyan")
        text.append("Automatically configures shell environment on start, and cleanly reverts on stop.\n\n", style="white")
        text.append("Press ", style="dim")
        text.append("[p]", style="bold cyan")
        text.append(" to start proxy daemon.\n\n", style="dim")
        border = "yellow"

    instructions = Text("[p] Toggle Start/Stop  |  [r] Refresh  |  [Esc/b] Back to Main Menu", style="dim cyan")
    return Panel(Group(text, instructions), title="[~] Auto-Rotation Proxy Controller", border_style=border, box=DEFAULT_BOX)


def handle_proxy_key(tui, key: str) -> bool:
    """Handle keyboard navigation and toggles on proxy screen."""
    if key == KEY_QUIT:
        return True
    if key in (KEY_ESC, KEY_BACK):
        tui.current_screen = "main"
        tui.status_message = ""
        return False
    if key in ("p", "P"):
        if is_proxy_running():
            stop_proxy_daemon()
            tui.status_message = "[yellow]Local proxy daemon stopped.[/yellow]"
        else:
            ok, pid, msg = start_proxy_daemon()
            if ok:
                tui.status_message = f"[bold green][ok] Local proxy started (PID: {pid}) on http://{DEFAULT_PROXY_HOST}:{DEFAULT_PROXY_PORT}[/bold green]"
            else:
                tui.status_message = f"[red][x] {msg}[/red]"
        return False
    if key == KEY_REFRESH:
        tui.status_message = ""
        return False
    return False
