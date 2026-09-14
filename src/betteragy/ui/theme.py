"""Rich theme colors, visual progress bars, and formatters."""

from rich import box
from rich.style import Style
from rich.theme import Theme

DEFAULT_BOX = box.ROUNDED

BETTERAGY_THEME = Theme({
    "primary": "bold cyan",
    "secondary": "bold magenta",
    "success": "bold green",
    "warning": "bold yellow",
    "danger": "bold red",
    "dimmed": "dim white",
    "accent": "bold #38bdf8",
})


def render_progress_bar(percentage: int, width: int = 14) -> str:
    """Render a colored ASCII progress bar with threshold color grading."""
    pct = max(0, min(100, percentage))
    filled_len = int(round((pct / 100.0) * width))
    empty_len = width - filled_len

    if pct >= 50:
        color = "green"
    elif pct >= 20:
        color = "yellow"
    else:
        color = "red"

    bar = "█" * filled_len + "░" * empty_len
    return f"[{color}]{bar}[/{color}] {pct:>3}%"


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


def format_status_badge(is_active: bool, is_cooldown: bool, disabled: bool) -> str:
    """Render consistent status badge for account rows."""
    if disabled:
        return "[dim red]✖ Disabled[/dim red]"
    if is_cooldown:
        return "[yellow]⏳ Rate Limited[/yellow]"
    if is_active:
        return "[bold green]★ Active[/bold green]"
    return "[green]● Ready[/green]"
