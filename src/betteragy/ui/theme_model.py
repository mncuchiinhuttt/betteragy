"""ThemeDefinition data model and Rich theme converter."""

from dataclasses import dataclass
from rich.theme import Theme


@dataclass(frozen=True)
class ThemeDefinition:
    """Styling tokens and color palettes for terminal rendering."""

    id: str
    name: str
    description: str
    primary: str
    secondary: str
    border_style: str
    cursor_style: str
    title_style: str
    subtitle_style: str
    header_style: str
    sel_style: str
    dim_style: str
    quota_high: str
    quota_high_track: str
    quota_mid: str
    quota_mid_track: str
    quota_low: str
    quota_low_track: str
    active_badge: str
    ready_badge: str
    cooldown_badge: str
    disabled_badge: str

    def to_rich_theme(self) -> Theme:
        """Convert styling tokens into a Rich Console Theme."""
        return Theme({
            "primary": self.primary,
            "secondary": self.secondary,
            "success": f"bold {self.quota_high}",
            "warning": f"bold {self.quota_mid}",
            "danger": f"bold {self.quota_low}",
            "dimmed": self.dim_style,
            "accent": self.primary,
        })
