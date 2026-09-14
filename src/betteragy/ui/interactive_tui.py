"""Interactive arrow-key driven Terminal User Interface (TUI) for Betteragy."""

import sys
import time
from rich.console import Console, Group
from rich.panel import Panel
from rich.syntax import Syntax

from ..commands.shell_cmd import SHELL_SNIPPET
from ..services.account_service import AccountService
from ..services.quota_aggregator import QuotaAggregator
from ..services.quota_service import QuotaService
from ..services.rotation_service import RotationService
from ..services.usage_aggregator import UsageAggregator
from .cards import render_kpi_cards
from .interactive_screens import (
    MAIN_MENU_ITEMS,
    render_account_selector_panel,
    render_footer_hints,
    render_main_menu_panel,
)
from .key_listener import (
    KEY_BACK,
    KEY_DOWN,
    KEY_ENTER,
    KEY_ESC,
    KEY_QUIT,
    KEY_REFRESH,
    KEY_UP,
    KeyListener,
)
from .tables import render_quota_table, render_top_conversations_table
from .theme import BETTERAGY_THEME, DEFAULT_BOX


class InteractiveTUI:
    """Coordinates arrow-key navigation, screen transitions, and user actions."""

    def __init__(self):
        self.console = Console(theme=BETTERAGY_THEME)
        self.acc_svc = AccountService()
        self.quota_svc = QuotaService()
        self.quota_agg = QuotaAggregator(self.acc_svc, self.quota_svc)
        self.rot_svc = RotationService(self.acc_svc)
        self.usage_agg = UsageAggregator()

        self.current_screen = "main"
        self.menu_idx = 0
        self.account_idx = 0
        self.status_message = ""
        self.cached_quota = None
        self.cached_report = None

    def run(self) -> None:
        """Run the interactive alternate-screen navigation loop."""
        sys.stdout.write("\033[?1049h\033[?25l")
        sys.stdout.flush()

        try:
            with KeyListener() as listener:
                while True:
                    self._render_current_view()
                    key = listener.read_key()
                    if not key:
                        time.sleep(0.04)
                        continue

                    if self.current_screen == "main":
                        if self._handle_main_key(key):
                            break
                    elif self.current_screen == "switch_account":
                        if self._handle_switch_key(key):
                            break
                    elif self.current_screen in ("quota", "usage", "shell"):
                        if key == KEY_QUIT:
                            break
                        if key in (KEY_ESC, KEY_BACK, KEY_ENTER):
                            self.current_screen = "main"
                        elif key == KEY_REFRESH and self.current_screen == "quota":
                            self.cached_quota = None
        except KeyboardInterrupt:
            pass
        finally:
            sys.stdout.write("\033[?1049l\033[?25h")
            sys.stdout.flush()

    def _render_current_view(self) -> None:
        """Render the active screen to terminal."""
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

        elements = []
        if self.status_message:
            elements.append(Panel(self.status_message, style="bold green", box=DEFAULT_BOX))

        active_acc = self.acc_svc.get_active_account()
        active_email = active_acc.email if active_acc else "None"

        if self.current_screen == "main":
            elements.extend([render_main_menu_panel(self.menu_idx, active_email), render_footer_hints("main")])
        elif self.current_screen == "switch_account":
            accounts = self.acc_svc.get_accounts()
            elements.extend([render_account_selector_panel(accounts, self.account_idx, active_email), render_footer_hints("sub")])
        elif self.current_screen == "quota":
            if not self.cached_quota and active_acc:
                self.cached_quota = self.quota_agg.fetch_single_account(active_acc.email)
            if self.cached_quota:
                elements.append(render_quota_table(self.cached_quota))
            elements.append(render_footer_hints("sub"))
        elif self.current_screen == "usage":
            if not self.cached_report:
                self.cached_report = self.usage_agg.get_report(period="all")
            elements.append(render_kpi_cards(self.cached_report, active_acc))
            if self.cached_report.top_conversations:
                elements.append(render_top_conversations_table(self.cached_report))
            elements.append(render_footer_hints("sub"))
        elif self.current_screen == "shell":
            syntax = Syntax(SHELL_SNIPPET, "bash", theme="monokai", line_numbers=False)
            elements.extend([Panel(syntax, title="[bold cyan]🐚 Shell Integration[/bold cyan]", box=DEFAULT_BOX), render_footer_hints("sub")])

        self.console.print(Group(*elements))

    def _handle_main_key(self, key: str) -> bool:
        """Handle key input on main menu. Returns True to exit."""
        total_items = len(MAIN_MENU_ITEMS)
        if key in (KEY_UP, KEY_DOWN):
            delta = -1 if key == KEY_UP else 1
            self.menu_idx = (self.menu_idx + delta) % total_items
            self.status_message = ""
        elif key == KEY_QUIT:
            return True
        elif key == KEY_ESC:
            self.status_message = ""
        elif key == KEY_ENTER:
            return self._dispatch_action(MAIN_MENU_ITEMS[self.menu_idx][0])
        return False

    def _dispatch_action(self, action: str) -> bool:
        """Dispatch enter key action on selected main menu item."""
        self.status_message = ""
        if "Switch Account" in action:
            self.current_screen, self.account_idx = "switch_account", 0
        elif "Live AI Quotas" in action:
            self.cached_quota, self.current_screen = None, "quota"
        elif "Token Usage" in action:
            self.cached_report, self.current_screen = None, "usage"
        elif "Rotate Account" in action:
            ok, msg = self.rot_svc.rotate()
            self.status_message = f"[bold green]✓ {msg}[/bold green]" if ok else f"[red]✗ {msg}[/red]"
        elif "Set Cooldown" in action:
            ok, msg = self.rot_svc.set_cooldown(hours=4.0)
            self.status_message = f"[yellow]{msg}[/yellow]"
        elif "Add Account" in action:
            self.status_message = "To add an account, run: betteragy account add"
        elif "Remove Account" in action:
            self.status_message = "To remove an account, run: betteragy account remove <email>"
        elif "Shell Integration" in action:
            self.current_screen = "shell"
        elif "Exit" in action:
            return True
        return False

    def _handle_switch_key(self, key: str) -> bool:
        """Handle key input on account selector screen. Returns True to exit."""
        accounts = self.acc_svc.get_accounts()
        if not accounts:
            self.current_screen = "main"
            return False

        if key in (KEY_UP, KEY_DOWN):
            delta = -1 if key == KEY_UP else 1
            self.account_idx = (self.account_idx + delta) % len(accounts)
        elif key in (KEY_ESC, KEY_BACK):
            self.current_screen = "main"
        elif key == KEY_QUIT:
            return True
        elif key == KEY_ENTER:
            target = accounts[self.account_idx]
            ok, msg = self.acc_svc.switch_account(target.email)
            self.status_message = f"[bold green]✓ {msg}[/bold green]" if ok else f"[red]✗ {msg}[/red]"
            self.current_screen = "main"
        return False


def run_interactive_tui():
    """Launch the interactive TUI application."""
    app = InteractiveTUI()
    app.run()
