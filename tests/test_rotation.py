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
