"""Unit tests for OnboardingService state and setup orchestrator."""

import json
from pathlib import Path
import pytest

from betteragy.core.models import AccountRecord
from betteragy.services.onboarding_service import OnboardingService


class DummyAccountService:
    def __init__(self, accounts=None):
        self._accounts = accounts or []

    def get_accounts(self):
        return self._accounts

    def get_active_account(self):
        return self._accounts[0] if self._accounts else None

    def import_from_keychain(self):
        self._accounts.append(
            AccountRecord(
                email="dev@example.com",
                refresh_token="rt_123",
            )
        )
        return self._accounts


class DummyHarnessService:
    def __init__(self, installed=False, profile="strict"):
        self._installed = installed
        self._profile = profile

    def status(self):
        return {"installed": self._installed, "profile": self._profile}

    def install(self, profile="strict"):
        self._installed = True
        self._profile = profile
        return Path("/tmp/harness.md")


class DummyMCPRegistrar:
    def __init__(self, installed=False):
        self._installed = installed
        self.settings_path = "/tmp/mcp_config.json"

    def status(self):
        return {"installed": self._installed}

    def install(self, python_path=None):
        self._installed = True
        return {"installed": True}


def test_onboarding_state_lifecycle(tmp_path: Path):
    state_file = tmp_path / "onboarding.json"
    acc_svc = DummyAccountService()
    harness_svc = DummyHarnessService()
    mcp_reg = DummyMCPRegistrar()

    svc = OnboardingService(
        state_file=state_file,
        acc_svc=acc_svc,
        harness_svc=harness_svc,
        mcp_reg=mcp_reg,
    )

    # Initial: no state file and empty accounts -> onboarding needed
    assert svc.is_onboarding_needed() is True
    assert svc.get_state()["completed"] is False

    # Mark completed
    svc.mark_completed(profile="strict", notes="test")
    assert state_file.exists()
    assert svc.is_onboarding_needed() is False
    data = svc.get_state()
    assert data["completed"] is True
    assert data["harness_profile"] == "strict"

    # Reset
    ok = svc.reset()
    assert ok is True
    assert svc.is_onboarding_needed() is True


def test_onboarding_step_actions(tmp_path: Path):
    state_file = tmp_path / "onboarding.json"
    acc_svc = DummyAccountService()
    harness_svc = DummyHarnessService()
    mcp_reg = DummyMCPRegistrar()

    svc = OnboardingService(
        state_file=state_file,
        acc_svc=acc_svc,
        harness_svc=harness_svc,
        mcp_reg=mcp_reg,
    )

    # Step 1: Detect and import
    accs = svc.detect_and_import_accounts()
    assert len(accs) == 1
    assert accs[0]["email"] == "dev@example.com"

    # Step 2: Setup harness
    h_res = svc.setup_harness(profile="strict")
    assert h_res["success"] is True
    assert h_res["profile"] == "strict"

    # Step 3: Setup MCP
    m_res = svc.setup_mcp_server(python_path="/bin/python3")
    assert m_res["success"] is True

    # Step 5: Diagnostics
    diag = svc.run_diagnostics()
    assert diag["accounts_count"] == 1
    assert diag["active_account"] == "dev@example.com"
    assert diag["harness_installed"] is True
    assert diag["mcp_registered"] is True


def test_onboarding_wizard_non_interactive(tmp_path: Path):
    from betteragy.ui.onboarding_wizard import run_onboarding_wizard

    state_file = tmp_path / "onboarding.json"
    acc_svc = DummyAccountService()
    harness_svc = DummyHarnessService()
    mcp_reg = DummyMCPRegistrar()

    svc = OnboardingService(
        state_file=state_file,
        acc_svc=acc_svc,
        harness_svc=harness_svc,
        mcp_reg=mcp_reg,
    )
    ok = run_onboarding_wizard(svc, interactive=False)
    assert ok is True
    assert svc.is_onboarding_needed() is False
    assert state_file.exists()

