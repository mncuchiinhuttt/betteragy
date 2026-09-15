"""Rich theme colors, visual progress bars, and formatters."""

from rich import box
from rich.style import Style
from rich.theme import Theme

from .theme_catalog import ThemeDefinition
from .theme_manager import get_theme_manager

DEFAULT_BOX = box.ROUNDED


def get_current_rich_theme() -> Theme:
    """Get active Rich Theme from ThemeManager."""
    return get_theme_manager().get_rich_theme()


BETTERAGY_THEME = get_theme_manager().get_rich_theme()


def render_progress_bar(percentage: float | int, width: int = 14, theme: ThemeDefinition | None = None) -> str:
    """Render a smooth solid block progress bar next to percentage remaining."""
    w = max(1, width)
    pct = max(0, min(100, int(round(percentage))))
    filled_len = int(round((pct / 100.0) * w))
    empty_len = w - filled_len

    th = theme or get_theme_manager().get_active_theme()

    if pct >= 50:
        color = th.quota_high
        track_color = th.quota_high_track
    elif pct >= 20:
        color = th.quota_mid
        track_color = th.quota_mid_track
    else:
        color = th.quota_low
        track_color = th.quota_low_track

    filled_bar = f"[bold {color}]{'█' * filled_len}[/bold {color}]" if filled_len > 0 else ""
    empty_bar = f"[{track_color}]{'░' * empty_len}[/{track_color}]" if empty_len > 0 else ""

    return f"{filled_bar}{empty_bar} [bold {color}]{pct:>3}%[/bold {color}]"


def format_tokens(num: int) -> str:
    """Format large token numbers into readable abbreviated representations."""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def format_cost(amount_usd: float) -> str:
    """Format USD currency amount."""
    if amount_usd >= 100:
        return f"${amount_usd:.2f}"
    if amount_usd >= 1:
        return f"${amount_usd:.3f}"
    if amount_usd > 0:
        return f"${amount_usd:.4f}"
    return "$0.00"


def format_status_badge(is_active: bool, is_cooldown: bool, disabled: bool, theme: ThemeDefinition | None = None) -> str:
    """Render consistent ASCII status badge for account rows according to active theme."""
    th = theme or get_theme_manager().get_active_theme()
    if disabled:
        return th.disabled_badge
    if is_cooldown:
        return th.cooldown_badge
    if is_active:
        return th.active_badge
    return th.ready_badge
