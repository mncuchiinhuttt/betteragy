"""Unit tests for rotation strategies and rate-limit cooldown."""

import time
from unittest.mock import MagicMock
from betteragy.core.models import AccountRecord, AccountsStorage
from betteragy.services.account_service import AccountService
from betteragy.services.rotation_service import RotationService


def test_rotation_round_robin():
    acc1 = AccountRecord(email="acc1@gmail.com", refresh_token="rt1")
    acc2 = AccountRecord(email="acc2@gmail.com", refresh_token="rt2")
    acc3 = AccountRecord(email="acc3@gmail.com", refresh_token="rt3")

    mock_svc = MagicMock(spec=AccountService)
    mock_svc.get_storage.return_value = AccountsStorage(
        accounts=[acc1, acc2, acc3], active_email=acc1.email, rotate_strategy="round-robin"
    )
    mock_svc.get_accounts.return_value = [acc1, acc2, acc3]
    mock_svc.get_active_account.return_value = acc1

    rot = RotationService(mock_svc)
    target, _ = rot.select_next_account(strategy="round-robin")
    assert target == acc2


def test_rotation_cooldown_skips_rate_limited():
    now = time.time()
    acc1 = AccountRecord(email="acc1@gmail.com", refresh_token="rt1")
    acc2 = AccountRecord(email="acc2@gmail.com", refresh_token="rt2", cooldown_until=now + 3600)
    acc3 = AccountRecord(email="acc3@gmail.com", refresh_token="rt3")

    mock_svc = MagicMock(spec=AccountService)
    mock_svc.get_storage.return_value = AccountsStorage(
        accounts=[acc1, acc2, acc3], active_email=acc1.email, rotate_strategy="round-robin"
    )
    mock_svc.get_accounts.return_value = [acc1, acc2, acc3]
    mock_svc.get_active_account.return_value = acc1

    rot = RotationService(mock_svc)
    # acc2 is on cooldown, so it should skip acc2 and select acc3
    target, _ = rot.select_next_account(strategy="round-robin")
    assert target == acc3


def test_rotation_skips_exhausted_model_quota():
    """Verify select_next_account skips candidate accounts with 0% quota for requested model."""
    acc1 = AccountRecord(email="acc1@gmail.com", refresh_token="rt1")
    acc2 = AccountRecord(email="acc2@gmail.com", refresh_token="rt2")
    acc3 = AccountRecord(email="acc3@gmail.com", refresh_token="rt3")

    mock_svc = MagicMock(spec=AccountService)
    mock_svc.get_storage.return_value = AccountsStorage(
        accounts=[acc1, acc2, acc3], active_email=acc1.email, rotate_strategy="round-robin"
    )
    mock_svc.get_accounts.return_value = [acc1, acc2, acc3]
    mock_svc.get_active_account.return_value = acc1

    rot = RotationService(mock_svc)
    # Mock model quota: acc2 has 0%, acc3 has 55%
    rot.get_account_model_quota = MagicMock()
    rot.get_account_model_quota.side_effect = lambda acc, model: (0, "1h") if acc == acc2 else (55, "Ready")

    target, _ = rot.select_next_account(strategy="round-robin", model_id="claude-sonnet-4-6")
    # Should skip acc2 because of 0% quota and choose acc3
    assert target == acc3


def test_rotation_all_accounts_exhausted():
    """Verify select_next_account returns None with detailed breakdown when all accounts are 0%."""
    acc1 = AccountRecord(email="acc1@gmail.com", refresh_token="rt1")
    acc2 = AccountRecord(email="acc2@gmail.com", refresh_token="rt2")

    mock_svc = MagicMock(spec=AccountService)
    mock_svc.get_storage.return_value = AccountsStorage(
        accounts=[acc1, acc2], active_email=acc1.email, rotate_strategy="round-robin"
    )
    mock_svc.get_accounts.return_value = [acc1, acc2]
    mock_svc.get_active_account.return_value = acc1

    rot = RotationService(mock_svc)
    rot.get_account_model_quota = MagicMock()
    rot.get_account_model_quota.side_effect = lambda acc, model: (0, "4h 5m") if acc == acc1 else (0, "1d")

    target, msg = rot.select_next_account(strategy="round-robin", model_id="gemini-3.8-flash")
    assert target is None
    assert "depleted" in msg or "exhausted" in msg
    assert "resets in 4h 5m" in msg
    assert "resets in 1d" in msg
