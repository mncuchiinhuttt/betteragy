"""Background OAuth worker and interactive token import flows for Betteragy TUI."""

import sys
import threading
from typing import Optional

from ..core.models import AccountRecord
from ..services.account_service import AccountService
from ..services.oauth_service import fetch_user_info, refresh_access_token, start_oauth_flow


class OAuthWorker:
    """Runs Google OAuth 2.0 loopback server in background thread."""

    def __init__(self, port: int = 19876):
        self.port = port
        self.result: Optional[dict] = None
        self.done: bool = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Spawn background server and open user's default browser."""
        self.done = False
        self.result = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            self.result = start_oauth_flow(port=self.port, timeout_secs=120)
        except Exception:
            self.result = None
        finally:
            self.done = True


def save_oauth_account(acc_svc: AccountService, oauth_result: Optional[dict]) -> Optional[AccountRecord]:
    """Extract tokens and user info from oauth result and register in AccountService."""
    if not oauth_result:
        return None
    tokens = oauth_result.get("tokens", {})
    uinfo = oauth_result.get("user_info", {})
    email = uinfo.get("email")
    if not email or "refresh_token" not in tokens:
        return None

    rec = AccountRecord(
        email=email,
        name=uinfo.get("name", ""),
        picture=uinfo.get("picture", ""),
        refresh_token=tokens["refresh_token"],
        access_token=tokens.get("access_token", ""),
    )
    acc_svc.add_or_update_account(rec, make_active=True)
    return rec


def verify_and_save_token(acc_svc: AccountService, token: str) -> tuple[bool, str]:
    """Verify raw refresh token with Google and save as active account."""
    try:
        tokens = refresh_access_token(token.strip())
        uinfo = fetch_user_info(tokens["access_token"])
        email = uinfo.get("email")
        if not email:
            return False, "Failed to retrieve user email for token."

        rec = AccountRecord(
            email=email,
            name=uinfo.get("name", ""),
            picture=uinfo.get("picture", ""),
            refresh_token=token.strip(),
            access_token=tokens["access_token"],
        )
        acc_svc.add_or_update_account(rec, make_active=True)
        return True, f"Connected and activated: {email}"
    except Exception as e:
        return False, f"Invalid token: {e}"


from .key_listener import KEY_BACK, KEY_DOWN, KEY_ENTER, KEY_ESC, KEY_QUIT, KEY_UP


def prompt_token_input_terminal(acc_svc: AccountService) -> str:
    """Prompt user for refresh token by temporarily exiting raw buffer."""
    sys.stdout.write("\033[?1049l\033[?25h\n")
    sys.stdout.flush()
    try:
        print("=" * 56)
        print("  Connect Account via Google Refresh Token")
        print("=" * 56)
        token = input("Paste Google refresh_token (or press Enter to cancel): ").strip()
        if token:
            print("Verifying token with Google OAuth...")
            ok, msg = verify_and_save_token(acc_svc, token)
            return f"[bold green][ok] {msg}[/bold green]" if ok else f"[red][!] {msg}[/red]"
        return "[yellow]Token input cancelled.[/yellow]"
    except Exception as e:
        return f"[red][!] Error: {e}[/red]"
    finally:
        sys.stdout.write("\033[?1049h\033[?25l")
        sys.stdout.flush()


def handle_account_list_key(tui, key: str) -> bool:
    """Handle key input on account selector / remove screen."""
    accounts = tui.acc_svc.get_accounts()
    if not accounts:
        tui.current_screen = "main"
        return False

    if key in (KEY_UP, KEY_DOWN):
        delta = -1 if key == KEY_UP else 1
        tui.account_idx = (tui.account_idx + delta) % len(accounts)
    elif key in (KEY_ESC, KEY_BACK):
        tui.current_screen = "main"
    elif key == KEY_QUIT:
        return True
    elif key == KEY_ENTER:
        target = accounts[tui.account_idx]
        if tui.current_screen == "switch_account":
            ok, msg = tui.acc_svc.switch_account(target.email)
            tui.status_message = f"[bold green][ok] {msg}[/bold green]" if ok else f"[red][x] {msg}[/red]"
        else:
            tui.acc_svc.remove_account(target.email)
            tui.status_message = f"[bold green][ok] Removed account: {target.email}[/bold green]"
        tui.current_screen = "main"
    return False


def handle_add_account_key(tui, key: str) -> None:
    """Handle selection in Add Account screen."""
    if key in (KEY_UP, KEY_DOWN):
        delta = -1 if key == KEY_UP else 1
        tui.add_idx = (tui.add_idx + delta) % 2
    elif key in (KEY_ESC, KEY_BACK):
        tui.current_screen = "main"
    elif key == KEY_ENTER:
        if tui.add_idx == 0:
            tui.oauth_worker.start()
            tui.current_screen = "oauth_waiting"
        else:
            tui.status_message = prompt_token_input_terminal(tui.acc_svc)
            tui.current_screen = "main"


def finish_oauth(tui) -> None:
    """Process background OAuth completion."""
    rec = save_oauth_account(tui.acc_svc, tui.oauth_worker.result)
    if rec:
        tui.status_message = f"[bold green][ok] Connected account: {rec.email}[/bold green]"
    else:
        tui.status_message = "[red][!] Authentication cancelled or timed out.[/red]"
    tui.current_screen = "main"
