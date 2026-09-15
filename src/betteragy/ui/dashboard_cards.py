"""Dashboard status cards and mini quota widgets for the redesigned command center."""

from typing import Optional
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..core.models import AccountQuota, AccountRecord
from .theme import DEFAULT_BOX, format_status_badge, render_progress_bar
from .theme_manager import get_theme_manager


def render_active_overview_card(
    account: Optional[AccountRecord],
    proxy_active: bool,
    theme_name: str,
    account_count: int = 1,
    update_ver: Optional[str] = None,
) -> Panel:
    """Render high-contrast hero status card for current system state."""
    th = get_theme_manager().get_active_theme()
    t = Table(box=None, show_header=False, pad_edge=False, padding=(0, 1))
    t.add_column("Key", style=th.dim_style, width=15)
    t.add_column("Value", min_width=25)

    email = account.email if account else "No Account Linked"
    tier = (account.tier_name or account.tier or "Standard") if account else "None"
    t.add_row("Active Account", Text(email, style="bold white"))
    t.add_row("Google Tier", Text(f"Tier: {tier}", style=f"bold {th.primary}"))
    t.add_row("Account Pool", Text(f"{account_count} account(s) ready", style=th.secondary))

    p_badge = Text(f"[ok] Active (45124)", style=f"bold {th.quota_high}") if proxy_active else Text("[ ] Offline", style=th.dim_style)
    t.add_row("Auto-Rotate Proxy", p_badge)
    t.add_row("Color Theme", Text(f"[*] {theme_name.capitalize()}", style=th.primary))

    if update_ver:
        t.add_row("Update Notice", Text(f"[!] New v{update_ver} available", style=f"bold {th.quota_mid}"))

    return Panel(
        t,
        title=f"[{th.title_style}]:: System Overview ::[/{th.title_style}]",
        border_style=th.border_style,
        box=DEFAULT_BOX,
    )


def render_mini_quota_card(cached_quota: Optional[AccountQuota]) -> Panel:
    """Render compact real-time model quota bars directly on the dashboard."""
    th = get_theme_manager().get_active_theme()
    table = Table(box=None, show_header=False, pad_edge=False, padding=(0, 1))
    table.add_column("Model", style="bold white", width=20)
    table.add_column("Bar", width=22)
    table.add_column("Reset", style=th.dim_style, width=12)

    if not cached_quota or not cached_quota.buckets:
        msg = Text("  Live quota not cached.\n  Press [2] to refresh model limits.", style=th.dim_style)
        return Panel(
            msg,
            title=f"[{th.title_style}]:: Live Quota Snapshot ::[/{th.title_style}]",
            border_style=th.dim_style,
            box=DEFAULT_BOX,
        )

    # Show up to 4 key models
    display_buckets = cached_quota.buckets[:4]
    for b in display_buckets:
        pct = int(b.percentage)
        bar = render_progress_bar(pct, width=12)
        reset_str = b.reset_countdown or "Ready"
        m_name = (b.display_name or b.model_id)[:18]
        table.add_row(m_name, bar, reset_str)

    footer = Text("\n[*] Hint: Press [f] anytime to launch Quota Reset Fireworks! ✦", style=f"dim {th.primary}")
    from rich.console import Group
    content = Group(table, footer)

    return Panel(
        content,
        title=f"[{th.title_style}]:: Model Quota Snapshot ::[/{th.title_style}]",
        border_style=th.border_style,
        box=DEFAULT_BOX,
    )
