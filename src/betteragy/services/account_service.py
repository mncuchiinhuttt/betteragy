"""Account pool service: account CRUD, switching, and auto-import."""

import time
from datetime import datetime, timezone
from pathlib import Path
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
        """Get or lazily load accounts storage, auto-syncing from keyring."""
        if self._storage is None:
            self._storage = read_accounts_storage()
            self._auto_sync_from_keyring()
        return self._storage

    def import_from_omp(self) -> int:
        """Auto-import Google Antigravity accounts from Oh My Pi (OMP) credentials database."""
        omp_db = Path.home() / ".omp" / "agent" / "agent.db"
        if not omp_db.exists() or not self._storage:
            return 0
        imported = 0
        try:
            import sqlite3
            import json
            con = sqlite3.connect(str(omp_db), timeout=0.2)
            cur = con.cursor()
            cur.execute("SELECT data FROM auth_credentials WHERE provider = 'google-antigravity'")
            rows = cur.fetchall()
            con.close()
            existing = {a.email.lower(): a for a in self._storage.accounts}
            for (raw,) in rows:
                d = json.loads(raw)
                em, ref = d.get("email"), d.get("refresh")
                if em and ref and em.lower() not in existing:
                    acc = AccountRecord(
                        email=em, name=em.split("@")[0], refresh_token=ref,
                        access_token=d.get("access") or "", tier="g1-pro-tier", tier_name="Google AI Pro",
                    )
                    self._storage.accounts.append(acc)
                    existing[em.lower()] = acc
                    imported += 1
            if imported:
                write_accounts_storage(self._storage)
        except Exception:
            pass
        return imported

    def _auto_sync_from_keyring(self) -> None:
        """Inspect active keychain and OMP credentials, auto-importing new accounts."""
        if not self._storage: return
        self.import_from_omp()
        cred = KeyringAdapter.read_active_credential()
        if not cred or "token" not in cred: return
        t_info = cred["token"]
        rf, acc_tok = t_info.get("refresh_token"), t_info.get("access_token")
        if not rf or any(a.refresh_token == rf for a in self._storage.accounts): return
        try:
            uinfo = fetch_user_info(acc_tok) if acc_tok else None
            if not uinfo or "email" not in uinfo:
                tokens = refresh_access_token(rf); acc_tok = tokens.get("access_token"); uinfo = fetch_user_info(acc_tok)
            em = uinfo.get("email")
            if not em: return
            ex = next((a for a in self._storage.accounts if a.email.lower() == em.lower()), None)
            if ex:
                ex.refresh_token, ex.access_token = rf, acc_tok or ex.access_token
            else:
                self._storage.accounts.append(AccountRecord(
                    email=em, name=uinfo.get("name", ""), picture=uinfo.get("picture", ""),
                    refresh_token=rf, access_token=acc_tok or "", expiry=t_info.get("expiry", ""), last_used=time.time(),
                ))
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
            if record.access_token: existing.access_token = record.access_token
            if record.expiry: existing.expiry = record.expiry
            if record.name: existing.name = record.name
            if record.picture: existing.picture = record.picture
        else:
            storage.accounts.append(record)

        if make_active:
            storage.active_email = record.email
        write_accounts_storage(storage)
    def update_account_tier(self, email: str, tier_id: Optional[str], tier_name: Optional[str]) -> None:
        """Update and persist subscription tier metadata for an account."""
        storage = self.get_storage()
        acc = next((a for a in storage.accounts if a.email.lower() == email.lower()), None)
        if acc and (tier_id or tier_name):
            if tier_id: acc.tier = tier_id
            if tier_name: acc.tier_name = tier_name
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
            target.expiry = datetime.fromtimestamp(time.time() + expires_in, timezone.utc).isoformat()
            target.last_used = time.time()
            self._active_keyring.save_credentials(
                email=target.email,
                token=target.access_token,
                refresh_token=target.refresh_token,
                expiry=target.expiry,
            )
            if target.tier_name is None or target.tier is None:
                try:
                    from .quota_service import QuotaService
                    _, tid, tname = QuotaService().load_project_info(target.access_token)
                    self.update_account_tier(target.email, tid, tname)
                except Exception:
                    pass

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
            write_accounts_storage(self.get_storage())

        return account.access_token
