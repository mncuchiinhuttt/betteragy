"""Configuration management with atomic JSON persistence and security permissions."""

import json
import os
import tempfile
from pathlib import Path

from .constants import ACCOUNTS_FILE, CONFIG_DIR, LEGACY_ACCOUNTS_FILE
from .models import AccountRecord, AccountsStorage


def ensure_config_dir() -> Path:
    """Ensure ~/.config/betteragy exists with 0700 permissions."""
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(CONFIG_DIR, 0o700)
        except OSError:
            pass
    return CONFIG_DIR


def read_accounts_storage() -> AccountsStorage:
    """Read accounts storage from disk, auto-importing legacy accounts if needed."""
    ensure_config_dir()

    if not ACCOUNTS_FILE.exists():
        storage = AccountsStorage()
        # Attempt auto-import from legacy agysw accounts
        if LEGACY_ACCOUNTS_FILE.exists():
            try:
                with open(LEGACY_ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                    legacy_data = json.load(f)
                accounts_raw = legacy_data.get("accounts", [])
                active_idx = legacy_data.get("activeIndex", 0)
                imported_accounts: list[AccountRecord] = []
                for acc in accounts_raw:
                    email = acc.get("email")
                    rt = acc.get("refreshToken")
                    if email and rt:
                        imported_accounts.append(
                            AccountRecord(
                                email=email,
                                refresh_token=rt,
                                last_used=acc.get("lastUsed", 0.0),
                                cooldown_until=acc.get("cooldownUntil", 0.0),
                                disabled=acc.get("disabled", False),
                            )
                        )
                storage.accounts = imported_accounts
                if 0 <= active_idx < len(imported_accounts):
                    storage.active_email = imported_accounts[active_idx].email
                storage.rotate_strategy = legacy_data.get("rotateStrategy", "round-robin")
                write_accounts_storage(storage)
            except Exception:
                pass
        return storage

    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AccountsStorage.model_validate(data)
    except Exception:
        return AccountsStorage()


def write_accounts_storage(storage: AccountsStorage) -> None:
    """Write accounts storage atomically with 0600 file permissions."""
    ensure_config_dir()
    data = storage.model_dump()
    json_bytes = json.dumps(data, indent=2).encode("utf-8")

    fd, tmp_path = tempfile.mkstemp(dir=CONFIG_DIR, prefix="acc_tmp_")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(json_bytes)
        try:
            os.chmod(tmp_path, 0o600)
        except OSError:
            pass
        os.replace(tmp_path, ACCOUNTS_FILE)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
