"""Tests for HarnessService and rule template installation."""

from pathlib import Path
import pytest
from betteragy.harness.harness_service import HarnessService


def test_harness_install_and_status(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    gemini_md = tmp_path / "GEMINI.md"
    gemini_md.write_text("# Existing User Rules\n", encoding="utf-8")

    svc = HarnessService(rules_dir=rules_dir, gemini_md_path=gemini_md)
    assert svc.status()["installed"] is False

    path = svc.install(profile="strict")
    assert path.exists()

    stat = svc.status()
    assert stat["installed"] is True
    assert stat["profile"] == "strict"
    assert stat["size_bytes"] > 0
    assert stat["gemini_md_active"] is True

    # Check that GEMINI.md has preserved existing rules and added harness markers
    content = gemini_md.read_text(encoding="utf-8")
    assert "# Existing User Rules" in content
    assert "<!-- BETTERAGY_HARNESS_START -->" in content
    assert "<!-- BETTERAGY_HARNESS_END -->" in content

    # Install balanced profile (updates in place)
    svc.install(profile="balanced")
    assert svc.status()["profile"] == "balanced"
    content_balanced = gemini_md.read_text(encoding="utf-8")
    assert "Balanced Reasoning" in content_balanced


def test_harness_uninstall(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    gemini_md = tmp_path / "GEMINI.md"
    gemini_md.write_text("# Existing User Rules\n", encoding="utf-8")

    svc = HarnessService(rules_dir=rules_dir, gemini_md_path=gemini_md)
    svc.install(profile="strict")
    assert svc.status()["installed"] is True

    ok = svc.uninstall()
    assert ok is True
    assert svc.status()["installed"] is False

    # Check GEMINI.md has harness removed but original rules preserved
    content = gemini_md.read_text(encoding="utf-8")
    assert "# Existing User Rules" in content
    assert "<!-- BETTERAGY_HARNESS_START -->" not in content

    # Uninstall when already removed returns False
    assert svc.uninstall() is False
