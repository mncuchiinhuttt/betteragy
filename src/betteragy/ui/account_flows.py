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
