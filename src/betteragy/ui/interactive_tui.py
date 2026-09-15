"""Interactive arrow-key driven Terminal User Interface (TUI) for Betteragy."""

import sys
import time
from rich.console import Console, Group

from ..mcp.task_db import TaskDB
from ..proxy.daemon import is_proxy_running
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
from .menu_dispatcher import dispatch_main_menu_action
from .proxy_flows import handle_proxy_key
from .session_flows import handle_session_selector_key, handle_tasks_key
from .theme import BETTERAGY_THEME
from .theme_flows import handle_theme_key


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
        info = self.update_svc.check_for_updates(force=False)
        self.update_ver = info.latest_version if (info and info.is_newer) else None
        self.current_screen = "main"
        self.menu_idx = self.account_idx = self.add_idx = self.session_idx = self.session_tab_idx = self.theme_idx = 0
        self.selected_session_id = self.cached_quota = self.cached_report = self.last_quota = None
        self.status_message = ""

    def _is_proxy_active(self) -> bool:
        """Check whether local proxy daemon is running and healthy."""
        return is_proxy_running()

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
                    if key.startswith("CLICK:"):
                        from .mouse_handler import handle_mouse_click
                        _, x_s, y_s = key.split(":")
                        if handle_mouse_click(self, int(x_s), int(y_s)):
                            break
                        continue

                    if self.current_screen == "main":
                        if self._handle_main_key(key):
                            break
                    elif self.current_screen in ("switch_account", "remove_account"):
                        if self._handle_account_list_key(key):
                            break
                    elif self.current_screen == "add_account":
                        self._handle_add_account_key(key)
                    elif self.current_screen == "oauth_waiting":
                        if key in (KEY_ESC, KEY_BACK, KEY_QUIT):
                            self.current_screen = "main"
                            self.status_message = "[yellow]OAuth login cancelled.[/yellow]"
                    elif self.current_screen == "tasks":
                        if self._handle_tasks_key(key):
                            break
                    elif self.current_screen == "session_selector":
                        if self._handle_session_selector_key(key):
                            break
                    elif self.current_screen == "proxy":
                        if self._handle_proxy_key(key):
                            break
                    elif self.current_screen == "theme":
                        if self._handle_theme_key(key):
                            break
                    elif self.current_screen in ("quota", "usage", "shell", "harness"):
                        if key == KEY_QUIT:
                            break
                        if key in (KEY_ESC, KEY_BACK, KEY_ENTER):
                            self.current_screen = "main"
                        elif key == KEY_REFRESH:
                            if self.cached_quota:
                                self.last_quota = self.cached_quota
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

    def _fetch_active_quota(self, email: str):
        """Fetch quota and trigger celebration if any model quota reset from exhaustion."""
        old_q = self.last_quota or self.cached_quota
        new_q = self.quota_agg.fetch_single_account(email)
        if old_q and new_q and not new_q.is_error:
            from ..services.quota_service import detect_quota_resets
            resets = detect_quota_resets(old_q, new_q)
            if resets:
                from .fireworks import play_fireworks_celebration
                play_fireworks_celebration(self.console, title=f"AI Quota Restored: {', '.join(resets)}!")
        self.cached_quota, self.last_quota = new_q, None
        return new_q

    def _handle_main_key(self, key: str) -> bool:
        """Handle key input on main menu. Returns True to exit."""
        total = len(MAIN_MENU_ITEMS)
        if key in (KEY_UP, KEY_DOWN):
            delta = -1 if key == KEY_UP else 1
            self.menu_idx = (self.menu_idx + delta) % total
            self.status_message = ""
        elif key in (KEY_QUIT, "x", "X"):
            return True
        elif key in (KEY_ESC,):
            self.status_message = ""
        elif key in (KEY_ENTER,):
            return self._dispatch_action(MAIN_MENU_ITEMS[self.menu_idx][0])
        elif key in ("f", "F"):
            from .fireworks import play_fireworks_celebration
            play_fireworks_celebration(self.console, title="AI Quota Restored! 7-Day Limit Reset Celebration")
        elif key in ("p", "P"):
            self.current_screen = "proxy"
        elif key.isdigit() and 1 <= int(key) <= 9:
            idx = int(key) - 1
            if idx < total:
                self.menu_idx = idx
                return self._dispatch_action(MAIN_MENU_ITEMS[idx][0])
        elif key.lower() == "t":
            return self._dispatch_action("Theme")
        elif key.lower() == "u":
            return self._dispatch_action("Update")
        return False

    def _dispatch_action(self, action: str) -> bool:
        """Dispatch enter key action on selected main menu item."""
        return dispatch_main_menu_action(self, action)

    def _handle_account_list_key(self, key: str) -> bool:
        return handle_account_list_key(self, key)

    def _handle_add_account_key(self, key: str) -> None:
        handle_add_account_key(self, key)

    def _handle_tasks_key(self, key: str) -> bool:
        return handle_tasks_key(self, key)

    def _handle_session_selector_key(self, key: str) -> bool:
        return handle_session_selector_key(self, key)

    def _handle_proxy_key(self, key: str) -> bool:
        return handle_proxy_key(self, key)

    def _handle_theme_key(self, key: str) -> bool:
        return handle_theme_key(self, key)


def run_interactive_tui():
    """Launch the interactive TUI application."""
    app = InteractiveTUI()
    app.run()
