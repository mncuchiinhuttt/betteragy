"""Parallel quota aggregation across all configured accounts."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.models import AccountQuota
from .account_service import AccountService
from .quota_service import QuotaService


class QuotaAggregator:
    """Orchestrates parallel quota checks for multiple accounts."""

    def __init__(self, account_service: AccountService, quota_service: QuotaService):
        self.account_service = account_service
        self.quota_service = quota_service

    def fetch_single_account(self, email: str) -> AccountQuota:
        """Fetch quota for a single account by email, refreshing token if needed."""
        acc = self.account_service.find_account(email)
        if not acc:
            return AccountQuota(email=email, is_error=True, error_message="Account not found")

        try:
            token = self.account_service.ensure_valid_access_token(acc)
            return self.quota_service.fetch_quota(acc.email, token)
        except Exception as e:
            return AccountQuota(email=email, is_error=True, error_message=str(e))

    def fetch_all_accounts(self) -> list[AccountQuota]:
        """Fetch quotas for all tracked accounts concurrently."""
        accounts = self.account_service.get_accounts()
        if not accounts:
            return []

        results: dict[str, AccountQuota] = {}
        with ThreadPoolExecutor(max_workers=min(len(accounts), 8)) as executor:
            future_to_email = {
                executor.submit(self.fetch_single_account, acc.email): acc.email
                for acc in accounts
            }
            for future in as_completed(future_to_email):
                email = future_to_email[future]
                try:
                    results[email] = future.result()
                except Exception as e:
                    results[email] = AccountQuota(email=email, is_error=True, error_message=str(e))

        # Return in original account order
        return [results[acc.email] for acc in accounts if acc.email in results]
