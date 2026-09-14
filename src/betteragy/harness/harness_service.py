"""Service for managing the deep reasoning rule harness in agy."""

import re
from pathlib import Path
from typing import Any, Dict

from betteragy.harness.templates import get_harness_template

DEFAULT_RULES_DIR = Path.home() / ".gemini" / "config" / "rules"
DEFAULT_GEMINI_MD = Path.home() / ".gemini" / "GEMINI.md"
HARNESS_FILENAME = "betteragy-harness.md"
START_MARKER = "<!-- BETTERAGY_HARNESS_START -->"
END_MARKER = "<!-- BETTERAGY_HARNESS_END -->"


class HarnessService:
    """Manages installation, inspection, and removal of prompt rules."""

    def __init__(
        self,
        rules_dir: Path | None = None,
        gemini_md_path: Path | None = None,
    ) -> None:
        self.rules_dir = rules_dir or DEFAULT_RULES_DIR
        self.gemini_md_path = gemini_md_path if gemini_md_path is not None else DEFAULT_GEMINI_MD
        self.harness_file = self.rules_dir / HARNESS_FILENAME

    def _inject_gemini_md(self, content: str) -> bool:
        """Inject harness content into GEMINI.md with delimiter markers."""
        if not self.gemini_md_path or not self.gemini_md_path.parent.exists():
            return False
        try:
            existing = self.gemini_md_path.read_text(encoding="utf-8") if self.gemini_md_path.exists() else ""
            block = f"\n{START_MARKER}\n{content.strip()}\n{END_MARKER}\n"
            if START_MARKER in existing and END_MARKER in existing:
                pattern = re.compile(rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}\n?", re.DOTALL)
                updated = pattern.sub(block.strip() + "\n", existing)
            else:
                updated = (existing.rstrip() + "\n" + block) if existing else block.strip() + "\n"
            self.gemini_md_path.write_text(updated, encoding="utf-8")
            return True
        except OSError:
            return False

    def _remove_gemini_md(self) -> bool:
        """Remove harness content from GEMINI.md."""
        if not self.gemini_md_path or not self.gemini_md_path.exists():
            return False
        try:
            existing = self.gemini_md_path.read_text(encoding="utf-8")
            if START_MARKER in existing:
                pattern = re.compile(rf"\n?{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}\n?", re.DOTALL)
                updated = pattern.sub("", existing)
                self.gemini_md_path.write_text(updated, encoding="utf-8")
                return True
        except OSError:
            pass
        return False

    def install(self, profile: str = "strict") -> Path:
        """Install harness rules to agy rules directory and global GEMINI.md."""
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        content = get_harness_template(profile)
        self.harness_file.write_text(content, encoding="utf-8")
        self._inject_gemini_md(content)
        return self.harness_file

    def uninstall(self) -> bool:
        """Remove installed harness rule file and clean GEMINI.md."""
        removed_file = False
        if self.harness_file.exists():
            self.harness_file.unlink()
            removed_file = True
        removed_md = self._remove_gemini_md()
        return removed_file or removed_md

    def status(self) -> Dict[str, Any]:
        """Check current status of the harness across rules file and GEMINI.md."""
        installed = self.harness_file.exists()
        gemini_md_active = False
        if self.gemini_md_path and self.gemini_md_path.exists():
            try:
                gemini_md_active = START_MARKER in self.gemini_md_path.read_text(encoding="utf-8")
            except OSError:
                pass

        if not installed and not gemini_md_active:
            return {
                "installed": False,
                "path": str(self.harness_file),
                "profile": "none",
                "size_bytes": 0,
                "gemini_md_active": False,
            }

        content = ""
        if installed:
            try:
                content = self.harness_file.read_text(encoding="utf-8")
            except OSError:
                pass
        elif gemini_md_active and self.gemini_md_path:
            try:
                content = self.gemini_md_path.read_text(encoding="utf-8")
            except OSError:
                pass
        profile = "balanced" if "Balanced Reasoning" in content else "strict"
        return {
            "installed": True,
            "path": str(self.harness_file),
            "profile": profile,
            "size_bytes": len(content),
            "gemini_md_active": gemini_md_active,
        }
