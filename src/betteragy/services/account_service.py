"""Account pool service: account CRUD, switching, and auto-import."""

import time
from datetime import datetime, timezone
from typing import Optional

from ..core.config import read_accounts_storage, write_accounts_storage
from ..core.models import AccountRecord, AccountsStorage
from .keyring_adapter import KeyringAdapter
from .oauth_service import fetch_user_info, refresh_access_token


class AccountService:
    """Manages configured Antigravity accounts and active keyring injection."""

    def __init__(self):
        self._storage: Optional[AccountsStorage] = None

    def get_storage(self) -> AccountsStorage:
        """Get or lazily load accounts storage, auto-syncing from keyring if empty."""
        if self._storage is None:
            self._storage = read_accounts_storage()
            self._auto_import_from_keyring_if_empty()
        return self._storage

    def _auto_import_from_keyring_if_empty(self) -> None:
        """If storage has no accounts, try importing currently active keyring token."""
        if not self._storage or len(self._storage.accounts) > 0:
            return
        active_cred = KeyringAdapter.read_active_credential()
        if not active_cred or "token" not in active_cred:
            return
        token_info = active_cred["token"]
        refresh_token = token_info.get("refresh_token")
        access_token = token_info.get("access_token")
        if not refresh_token or not access_token:
            return
        try:
            uinfo = fetch_user_info(access_token)
            email = uinfo.get("email")
            if email:
                acc = AccountRecord(
                    email=email,
                    name=uinfo.get("name", ""),
                    picture=uinfo.get("picture", ""),
                    refresh_token=refresh_token,
                    access_token=access_token,
                    expiry=token_info.get("expiry", ""),
                    last_used=time.time(),
                )
                self._storage.accounts.append(acc)
                self._storage.active_email = email
                write_accounts_storage(self._storage)
        except Exception:
            pass

    def get_accounts(self) -> list[AccountRecord]:
        return self.get_storage().accounts

    def get_active_account(self) -> Optional[AccountRecord]:
        storage = self.get_storage()
        if not storage.active_email:
            return storage.accounts[0] if storage.accounts else None
        for acc in storage.accounts:
            if acc.email.lower() == storage.active_email.lower():
                return acc
        return storage.accounts[0] if storage.accounts else None

    def add_or_update_account(self, record: AccountRecord, make_active: bool = True) -> None:
        storage = self.get_storage()
        existing = next((a for a in storage.accounts if a.email.lower() == record.email.lower()), None)
        if existing:
            existing.refresh_token = record.refresh_token
            if record.access_token:
                existing.access_token = record.access_token
            if record.expiry:
                existing.expiry = record.expiry
            if record.name:
                existing.name = record.name
            if record.picture:
                existing.picture = record.picture
        else:
            storage.accounts.append(record)

        if make_active:
            storage.active_email = record.email
        write_accounts_storage(storage)

    def remove_account(self, identifier: str) -> bool:
        storage = self.get_storage()
        acc = self.find_account(identifier)
        if not acc:
            return False
        storage.accounts = [a for a in storage.accounts if a.email.lower() != acc.email.lower()]
        if storage.active_email and storage.active_email.lower() == acc.email.lower():
            storage.active_email = storage.accounts[0].email if storage.accounts else None
        write_accounts_storage(storage)
        return True

    def find_account(self, identifier: str) -> Optional[AccountRecord]:
        storage = self.get_storage()
        try:
            idx = int(identifier) - 1
            if 0 <= idx < len(storage.accounts):
                return storage.accounts[idx]
        except ValueError:
            pass
        norm = identifier.strip().lower()
        for acc in storage.accounts:
            if acc.email.lower() == norm or acc.email.lower().startswith(norm):
                return acc
        return None

    def switch_account(self, identifier: str) -> tuple[bool, str]:
        """Switch active account, proactively refresh access token and write to keyring."""
        storage = self.get_storage()
        target = self.find_account(identifier)
        if not target:
            return False, f"Account '{identifier}' not found in your pool."

        try:
            tokens = refresh_access_token(target.refresh_token)
            target.access_token = tokens["access_token"]
            expires_in = tokens.get("expires_in", 3600)
            expiry_dt = datetime.fromtimestamp(time.time() + expires_in, timezone.utc)
            target.expiry = expiry_dt.isoformat()
            target.last_used = time.time()
            if "refresh_token" in tokens:
                target.refresh_token = tokens["refresh_token"]

            KeyringAdapter.write_credential(
                access_token=target.access_token,
                refresh_token=target.refresh_token,
                expiry=target.expiry,
            )

            storage.active_email = target.email
            write_accounts_storage(storage)
            return True, f"Switched active Antigravity account to: {target.email}"
        except Exception as e:
            return False, f"Failed to switch account: {e}"

    def ensure_valid_access_token(self, account: AccountRecord) -> str:
        """Ensure account has a valid access token, refreshing if necessary."""
        need_refresh = not account.access_token or not account.expiry
        if not need_refresh:
            try:
                exp_ts = datetime.fromisoformat(account.expiry).timestamp()
                if time.time() > (exp_ts - 300):
                    need_refresh = True
            except Exception:
                need_refresh = True

        if need_refresh:
            tokens = refresh_access_token(account.refresh_token)
            account.access_token = tokens["access_token"]
            expires_in = tokens.get("expires_in", 3600)
            account.expiry = datetime.fromtimestamp(time.time() + expires_in, timezone.utc).isoformat()
            if "refresh_token" in tokens:
                account.refresh_token = tokens["refresh_token"]
            storage = self.get_storage()
            write_accounts_storage(storage)

        return account.access_token
