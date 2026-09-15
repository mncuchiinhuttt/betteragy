"""Onboarding state management and subsystem configuration service for Betteragy."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..harness.harness_service import HarnessService
from ..mcp.mcp_registrar import MCPRegistrar
from .account_service import AccountService

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "betteragy"
DEFAULT_ONBOARDING_FILE = DEFAULT_CONFIG_DIR / "onboarding.json"


class OnboardingService:
    """Orchestrates first-run detection, system setup steps, and onboarding state."""

    def __init__(
        self,
        state_file: Optional[Path] = None,
        acc_svc: Optional[AccountService] = None,
        harness_svc: Optional[HarnessService] = None,
        mcp_reg: Optional[MCPRegistrar] = None,
    ) -> None:
        self.state_file = state_file or DEFAULT_ONBOARDING_FILE
        self.acc_svc = acc_svc or AccountService()
        self.harness_svc = harness_svc or HarnessService()
        self.mcp_reg = mcp_reg or MCPRegistrar()

    def get_state(self) -> Dict[str, Any]:
        """Read saved onboarding state from disk."""
        if not self.state_file.exists():
            return {"completed": False, "first_run": True, "steps": {}}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"completed": False, "first_run": True, "steps": {}}

    def is_onboarding_needed(self) -> bool:
        """Return True if user has never finished onboarding or state file is missing."""
        state = self.get_state()
        if state.get("completed"):
            return False
        # If user already has accounts and harness installed manually, mark as completed
        accs = self.acc_svc.get_accounts()
        harness_stat = self.harness_svc.status()
        if accs and harness_stat.get("installed"):
            self.mark_completed(notes="auto_detected_existing_setup")
            return False
        return True

    def mark_completed(self, profile: str = "strict", notes: str = "") -> None:
        """Persist onboarding completion state."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "completed": True,
            "first_run": False,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "harness_profile": profile,
            "notes": notes,
        }
        self.state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def reset(self) -> bool:
        """Clear onboarding state to trigger first-run setup again."""
        if self.state_file.exists():
            self.state_file.unlink()
            return True
        return False

    def detect_and_import_accounts(self) -> List[Dict[str, Any]]:
        """Auto-detect accounts in Keychain and import them into Betteragy pool."""
        try:
            self.acc_svc.import_from_keychain()
        except Exception:
            pass
        active = self.acc_svc.get_active_account()
        active_email = active.email if active else None
        return [
            {"email": a.email, "active": (a.email == active_email)}
            for a in self.acc_svc.get_accounts()
        ]

    def setup_harness(self, profile: str = "strict") -> Dict[str, Any]:
        """Install Deep Reasoning Harness into agy rules and global GEMINI.md."""
        installed_path = self.harness_svc.install(profile=profile)
        stat = self.harness_svc.status()
        return {"success": True, "path": str(installed_path), "profile": stat.get("profile", profile)}

    def setup_mcp_server(self, python_path: Optional[str] = None) -> Dict[str, Any]:
        """Register betteragy-todo stdio server in ~/.gemini/config/mcp_config.json."""
        res = self.mcp_reg.install(python_path=python_path or sys.executable)
        return {"success": True, "settings_path": self.mcp_reg.settings_path, "status": res}

    def setup_shell_alias(self) -> Dict[str, Any]:
        """Configure agy alias with maximum reasoning effort and skip permissions in shell profile."""
        zshrc = Path.home() / ".zshrc"
        bashrc = Path.home() / ".bashrc"
        target = zshrc if zshrc.exists() else bashrc

        alias_line = 'alias agy="agy --effort high --dangerously-skip-permissions"\n'
        if target.exists():
            content = target.read_text(encoding="utf-8", errors="ignore")
            if "alias agy=" in content or "agy()" in content:
                return {"success": True, "target": str(target), "already_existed": True}

        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as f:
            f.write(f"\n# Betteragy deep thinking alias\n{alias_line}")
        return {"success": True, "target": str(target), "already_existed": False}

    def run_diagnostics(self) -> Dict[str, Any]:
        """Verify health across all Betteragy subsystems."""
        accounts = self.acc_svc.get_accounts()
        active = self.acc_svc.get_active_account()
        harness = self.harness_svc.status()
        mcp_status = self.mcp_reg.status()

        zshrc = Path.home() / ".zshrc"
        bashrc = Path.home() / ".bashrc"
        target = zshrc if zshrc.exists() else bashrc
        alias_configured = False
        if target.exists():
            alias_configured = "alias agy=" in target.read_text(encoding="utf-8", errors="ignore")

        return {
            "accounts_count": len(accounts),
            "active_account": active.email if active else None,
            "harness_installed": harness.get("installed", False),
            "harness_profile": harness.get("profile", "none"),
            "mcp_registered": mcp_status.get("installed", False),
            "shell_alias_configured": alias_configured,
            "target_shell_file": str(target),
        }
