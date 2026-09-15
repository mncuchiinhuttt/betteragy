"""Rotation strategies and rate-limit cooldown management."""

import random
import time
from typing import Optional

from ..core.config import write_accounts_storage
from ..core.models import AccountRecord
from .account_service import AccountService


class RotationService:
    """Handles automatic rotation across healthy accounts."""

    def __init__(self, account_service: AccountService, quota_service: Optional[object] = None):
        self.account_service = account_service
        self._quota_service = quota_service

    def _get_quota_service(self):
        if self._quota_service is None:
            from .quota_service import QuotaService
            self._quota_service = QuotaService()
        return self._quota_service

    def get_account_model_quota(self, account: AccountRecord, model_id: str) -> tuple[int, str]:
        """Return (percentage, countdown) for specific model on an account."""
        try:
            token = self.account_service.ensure_valid_access_token(account)
            q_svc = self._get_quota_service()
            q = q_svc.fetch_quota(account.email, token)
            if q.is_error or q.is_forbidden or not q.buckets:
                return 0, "Unavailable"
            m_norm = model_id.lower().replace("_", "-").replace(" ", "-")
            for b in q.buckets:
                b_norm = b.model_id.lower().replace("_", "-")
                d_norm = b.display_name.lower().replace(" ", "-")
                if m_norm in b_norm or b_norm in m_norm or m_norm in d_norm or d_norm in m_norm:
                    return int(b.percentage), b.reset_countdown or "Ready"
            return 100, "Ready"
        except Exception:
            return 100, "Ready"

    def get_healthy_accounts(self) -> list[AccountRecord]:
        """Return list of accounts that are enabled and not in cooldown."""
        now = time.time()
        accounts = self.account_service.get_accounts()
        return [a for a in accounts if not a.disabled and (a.cooldown_until <= now)]

    def select_next_account(
        self, strategy: Optional[str] = None, force: bool = False, model_id: Optional[str] = None
    ) -> tuple[Optional[AccountRecord], str]:
        """Select next account with available quota for model_id."""
        storage = self.account_service.get_storage()
        strat = strategy or storage.rotate_strategy or "round-robin"
        healthy = self.get_healthy_accounts()
        active = self.account_service.get_active_account()

        if not healthy:
            return None, "All accounts are currently in rate-limit cooldown or disabled."

        # Filter out accounts that have 0% quota for the requested model
        if model_id and len(healthy) > 0:
            with_quota = []
            exhausted_details = []
            for a in healthy:
                pct, countdown = self.get_account_model_quota(a, model_id)
                if pct > 0:
                    with_quota.append(a)
                else:
                    exhausted_details.append(f"{a.email}: {pct}% (resets in {countdown})")
            if with_quota:
                healthy = with_quota
            else:
                summary = "; ".join(exhausted_details) if exhausted_details else "All accounts at 0% quota."
                return None, f"All pool accounts depleted for '{model_id}'. Status: {summary}"
        if strat == "sticky" and active in healthy and not force:
            return active, f"Sticky strategy: staying on healthy account {active.email}."

        if strat == "least-used":
            candidates = [a for a in healthy if a != active or len(healthy) == 1]
            candidates.sort(key=lambda a: a.last_used)
            target = candidates[0]
            return target, f"Selected least-used account: {target.email}"

        if strat == "random":
            pool = [a for a in healthy if a != active or len(healthy) == 1]
            target = random.choice(pool)
            return target, f"Randomly selected account: {target.email}"

        # Default: round-robin
        accounts = storage.accounts
        curr_idx = accounts.index(active) if active in accounts else -1
        # Find next healthy index past curr_idx
        healthy_indices = [i for i, a in enumerate(accounts) if a in healthy]
        next_indices = [i for i in healthy_indices if i > curr_idx]
        target_idx = next_indices[0] if next_indices else healthy_indices[0]
        target = accounts[target_idx]

        if target == active and not force and len(healthy) == 1:
            return target, f"Only 1 healthy account ({target.email}); staying active."

        return target, f"Selected next account (round-robin): {target.email}"

    def rotate(
        self, strategy: Optional[str] = None, force: bool = False, model_id: Optional[str] = None
    ) -> tuple[bool, str]:
        """Advance to next healthy account with quota for model_id."""
        target, msg = self.select_next_account(strategy=strategy, force=force, model_id=model_id)
        if not target:
            return False, msg
        active = self.account_service.get_active_account()
        if target == active and not force:
            return True, msg
        return self.account_service.switch_account(target.email)

    def set_cooldown(self, hours: float = 4.0, model_id: Optional[str] = None) -> tuple[bool, str]:
        """Mark active account in rate-limit cooldown for N hours, then rotate."""
        active = self.account_service.get_active_account()
        if not active:
            return False, "No active account found to place on cooldown."

        cooldown_until = time.time() + (hours * 3600)
        active.cooldown_until = cooldown_until
        storage = self.account_service.get_storage()
        write_accounts_storage(storage)

        # Rotate to next healthy account with model quota
        success, rot_msg = self.rotate(force=True, model_id=model_id)
        until_str = time.strftime("%H:%M:%S", time.localtime(cooldown_until))
        msg = f"Marked {active.email} on cooldown for {hours:.1f}h (until {until_str}).\n{rot_msg}"
        return success, msg
