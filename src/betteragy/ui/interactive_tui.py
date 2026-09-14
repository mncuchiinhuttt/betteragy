"""Interactive arrow-key driven Terminal User Interface (TUI) for Betteragy."""

import sys
import time
from rich.console import Console, Group

from ..mcp.task_db import TaskDB
from ..services.account_service import AccountService
from ..services.quota_aggregator import QuotaAggregator
from ..services.quota_service import QuotaService
from ..services.rotation_service import RotationService
from ..services.update_service import UpdateService
from ..services.usage_aggregator import UsageAggregator
from .account_flows import OAuthWorker, finish_oauth, handle_account_list_key, handle_add_account_key
from .interactive_renderer import build_screen_elements
from .interactive_screens import MAIN_MENU_ITEMS
from .key_listener import KEY_BACK, KEY_DOWN, KEY_ENTER, KEY_ESC, KEY_QUIT, KEY_REFRESH, KEY_UP, KeyListener
from .session_flows import handle_session_selector_key, handle_tasks_key
from .theme import BETTERAGY_THEME


class InteractiveTUI:
    """Coordinates arrow-key navigation, screen transitions, and user actions."""

    def __init__(self):
        self.console = Console(theme=BETTERAGY_THEME)
        self.acc_svc = AccountService()
        self.quota_svc = QuotaService()
        self.quota_agg = QuotaAggregator(self.acc_svc, self.quota_svc)
        self.rot_svc = RotationService(self.acc_svc)
        self.usage_agg = UsageAggregator()
        self.oauth_worker = OAuthWorker()
        self.task_db = TaskDB()
        self.update_svc = UpdateService()
        self.update_ver = None
        info = self.update_svc.check_for_updates(force=False)
        if info and info.is_newer:
            self.update_ver = info.latest_version

        self.current_screen = "main"
        self.menu_idx = 0
        self.account_idx = 0
        self.add_idx = 0
        self.session_idx = 0
        self.session_tab_idx = 0
        self.selected_session_id = None
        self.status_message = ""
        self.cached_quota = None
        self.cached_report = None

    def run(self) -> None:
        """Run the interactive alternate-screen navigation loop."""
        sys.stdout.write("\033[?1049h\033[?25l")
        sys.stdout.flush()

        try:
            with KeyListener() as listener:
                needs_redraw = True
                while True:
                    if needs_redraw:
                        self._render_current_view()
                        needs_redraw = False

                    key = listener.read_key()
                    if not key:
                        if self.current_screen == "oauth_waiting" and self.oauth_worker.done:
                            finish_oauth(self)
                            needs_redraw = True
                        time.sleep(0.03)
                        continue

                    needs_redraw = True
                    if self.current_screen == "main":
                        if self._handle_main_key(key):
                            break
                    elif self.current_screen in ("switch_account", "remove_account"):
                        if handle_account_list_key(self, key):
                            break
                    elif self.current_screen == "add_account":
                        handle_add_account_key(self, key)
                    elif self.current_screen == "oauth_waiting":
                        if key in (KEY_ESC, KEY_BACK, KEY_QUIT):
                            self.current_screen = "main"
                            self.status_message = "[yellow]OAuth login cancelled.[/yellow]"
                    elif self.current_screen == "tasks":
                        if handle_tasks_key(self, key):
                            break
                    elif self.current_screen == "session_selector":
                        if handle_session_selector_key(self, key):
                            break
                    elif self.current_screen in ("quota", "usage", "shell", "harness"):
                        if key == KEY_QUIT:
                            break
                        if key in (KEY_ESC, KEY_BACK, KEY_ENTER):
                            self.current_screen = "main"
                        elif key == KEY_REFRESH:
                            self.cached_quota, self.cached_report = None, None

        except KeyboardInterrupt:
            pass
        finally:
            sys.stdout.write("\033[?1049l\033[?25h")
            sys.stdout.flush()

    def _render_current_view(self) -> None:
        """Render active screen elements to terminal."""
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
        elements = build_screen_elements(self)
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
        elif "Add Account" in action:
            self.current_screen, self.add_idx = "add_account", 0
        elif "Remove Account" in action:
            accounts = self.acc_svc.get_accounts()
            if not accounts:
                self.status_message = "[yellow]No accounts in pool to remove.[/yellow]"
            else:
                self.current_screen, self.account_idx = "remove_account", 0
        elif "Live AI Quotas" in action:
            self.cached_quota, self.current_screen = None, "quota"
        elif "Token Usage" in action:
            self.cached_report, self.current_screen = None, "usage"
        elif "Rotate Account" in action:
            ok, msg = self.rot_svc.rotate()
            self.status_message = f"[bold green][ok] {msg}[/bold green]" if ok else f"[red][x] {msg}[/red]"
        elif "Set Cooldown" in action:
            ok, msg = self.rot_svc.set_cooldown(hours=4.0)
            self.status_message = f"[yellow]{msg}[/yellow]"
        elif "Tasks" in action:
            self.current_screen = "tasks"
        elif "Harness" in action:
            self.current_screen = "harness"
        elif "Shell Integration" in action:
            self.current_screen = "shell"
        elif "Updates" in action:
            info = self.update_svc.check_for_updates(force=True)
            if info and info.is_newer:
                self.update_ver = info.latest_version
                self.status_message = f"[bold yellow][!] Update available: v{info.latest_version}[/bold yellow] (Run: betteragy update)"
            elif info:
                self.status_message = f"[bold green][ok] Betteragy is up to date (v{info.current_version})[/bold green]"
            else:
                self.status_message = "[yellow][!] Could not check for updates (offline)[/yellow]"
        elif "Exit" in action:
            return True
        return False

    def _handle_account_list_key(self, key: str) -> bool:
        return handle_account_list_key(self, key)

    def _handle_add_account_key(self, key: str) -> None:
        handle_add_account_key(self, key)

    def _handle_tasks_key(self, key: str) -> bool:
        return handle_tasks_key(self, key)

    def _handle_session_selector_key(self, key: str) -> bool:
        return handle_session_selector_key(self, key)


def run_interactive_tui():
    """Launch the interactive TUI application."""
    app = InteractiveTUI()
    app.run()

