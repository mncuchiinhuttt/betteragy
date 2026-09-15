"""Theme manager service for Betteragy styling and persistence."""

from typing import Optional
from rich.theme import Theme

from ..core.config import read_accounts_storage, write_accounts_storage
from .theme_catalog import THEME_CATALOG, ThemeDefinition

DEFAULT_THEME_ID = "warm"


class ThemeManager:
    """Manages active theme, catalog lookup, and storage persistence."""

    def __init__(self):
        self._active_id: Optional[str] = None

    def get_active_theme_id(self) -> str:
        """Return the active theme ID, loading from config if not cached."""
        if not self._active_id:
            try:
                storage = read_accounts_storage()
                self._active_id = getattr(storage, "theme", DEFAULT_THEME_ID) or DEFAULT_THEME_ID
            except Exception:
                self._active_id = DEFAULT_THEME_ID
        if self._active_id not in THEME_CATALOG:
            self._active_id = DEFAULT_THEME_ID
        return self._active_id

    def get_active_theme(self) -> ThemeDefinition:
        """Return the active ThemeDefinition instance."""
        theme_id = self.get_active_theme_id()
        return THEME_CATALOG.get(theme_id, THEME_CATALOG[DEFAULT_THEME_ID])

    def set_active_theme(self, theme_id: str) -> bool:
        """Set active theme and persist to accounts storage."""
        if theme_id not in THEME_CATALOG:
            return False
        self._active_id = theme_id
        try:
            storage = read_accounts_storage()
            storage.theme = theme_id
            write_accounts_storage(storage)
        except Exception:
            pass
        return True

    def get_theme(self, theme_id: str) -> Optional[ThemeDefinition]:
        """Look up a ThemeDefinition by ID."""
        return THEME_CATALOG.get(theme_id)

    def list_themes(self) -> list[ThemeDefinition]:
        """List all available ThemeDefinitions."""
        return list(THEME_CATALOG.values())

    def get_rich_theme(self) -> Theme:
        """Build Rich Theme corresponding to the currently active theme."""
        return self.get_active_theme().to_rich_theme()


_global_theme_mgr = ThemeManager()


def get_theme_manager() -> ThemeManager:
    """Return the global ThemeManager singleton."""
    return _global_theme_mgr
