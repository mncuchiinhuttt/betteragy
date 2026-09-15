"""Rich table builders for accounts, quotas, and conversation metrics."""

import time
from typing import Optional
from rich.table import Table

from ..core.models import AccountQuota, AccountRecord, DeepUsageReport
from .theme import DEFAULT_BOX, format_cost, format_status_badge, format_tier_name, format_tokens, render_progress_bar
from .theme_manager import get_theme_manager


def render_accounts_table(accounts: list[AccountRecord], active_email: Optional[str]) -> Table:
    """Build a styled table listing all configured accounts."""
    th = get_theme_manager().get_active_theme()
    table = Table(
        title=f"[{th.title_style}]Antigravity Multi-Account Switchboard[/{th.title_style}]",
        box=DEFAULT_BOX,
        header_style=th.header_style,
        title_justify="left",
        expand=True,
    )
    table.add_column("#", style=th.dim_style, justify="right", width=3)
    table.add_column("Account / Email", style="bold white", min_width=25)
    table.add_column("Status", justify="center", width=16)
    table.add_column("Tier", style=th.secondary, width=18)
    table.add_column("Last Switched", style=th.dim_style, justify="right", width=16)

    now = time.time()
    for idx, acc in enumerate(accounts, 1):
        is_active = bool(active_email and acc.email.lower() == active_email.lower())
        is_cooldown = acc.cooldown_until > now
        badge = format_status_badge(is_active, is_cooldown, acc.disabled, theme=th)
        tier_str = format_tier_name(acc.tier_name, acc.tier)

        last_str = "Never"
        if acc.last_used > 0:
            diff = now - acc.last_used
            if diff < 3600:
                last_str = f"{int(diff // 60)}m ago"
            elif diff < 86400:
                last_str = f"{int(diff // 3600)}h ago"
            else:
                last_str = f"{int(diff // 86400)}d ago"

        row_style = th.sel_style if is_active else None
        table.add_row(str(idx), acc.email, badge, tier_str, last_str, style=row_style)

    return table


def render_quota_table(quota: AccountQuota) -> Table:
    """Build a table displaying model quota buckets and reset timers."""
    th = get_theme_manager().get_active_theme()
    tier_info = f" ({format_tier_name(quota.tier_name, quota.tier)})" if (quota.tier_name or quota.tier) else ""
    title = f"[{th.title_style}]AI Model Quota — {quota.email}{tier_info}[/{th.title_style}]"
    table = Table(title=title, box=DEFAULT_BOX, header_style=th.header_style, title_justify="left", expand=True)

    table.add_column("Model", style="bold white", min_width=28)
    table.add_column("Available Quota", min_width=24)
    table.add_column("Reset Time", style=th.secondary, justify="center", width=12)
    table.add_column("Countdown", style=th.primary, justify="right", width=14)

    if quota.is_error:
        table.add_row(f"[{th.quota_low}]Error[/{th.quota_low}]", f"[{th.quota_low}]{quota.error_message}[/{th.quota_low}]", "-", "-")
        return table

    if quota.is_forbidden:
        table.add_row(f"[{th.quota_mid}]Forbidden[/{th.quota_mid}]", "No Code Assist quota granted", "-", "-")
        return table

    for b in quota.buckets:
        bar = render_progress_bar(b.percentage, theme=th)
        table.add_row(b.display_name, bar, b.reset_time_str or "-", b.reset_countdown or "Ready")

    return table


def render_multi_quota_matrix(quotas: list[AccountQuota]) -> Table:
    """Build a matrix table comparing model quotas across all accounts side-by-side."""
    th = get_theme_manager().get_active_theme()
    table = Table(
        title=f"[{th.title_style}]Live Quota Matrix Across All Accounts[/{th.title_style}]",
        box=DEFAULT_BOX,
        header_style=th.header_style,
        title_justify="left",
    )
    table.add_column("Model", style="bold white", min_width=26)
    for q in quotas:
        short_email = q.email.split("@")[0]
        table.add_column(short_email, justify="center", min_width=18)

    all_models: dict[str, str] = {}
    for q in quotas:
        for b in q.buckets:
            all_models[b.model_id] = b.display_name

    for model_id, display_name in sorted(all_models.items(), key=lambda x: x[1]):
        row = [display_name]
        for q in quotas:
            bucket = next((b for b in q.buckets if b.model_id == model_id), None)
            if bucket:
                row.append(render_progress_bar(bucket.percentage, width=8, theme=th))
            else:
                row.append(f"[{th.dim_style}]--[/{th.dim_style}]")
        table.add_row(*row)

    return table


def render_top_conversations_table(report: DeepUsageReport) -> Table:
    """Build a table showing the heaviest token-consuming conversations."""
    th = get_theme_manager().get_active_theme()
    table = Table(
        title=f"[{th.title_style}]Top Conversations by Token & Cost Usage[/{th.title_style}]",
        box=DEFAULT_BOX,
        header_style=th.header_style,
        title_justify="left",
        expand=True,
    )
    table.add_column("#", style=th.dim_style, justify="right", width=3)
    table.add_column("Conversation", style="bold white", no_wrap=True, max_width=32)
    table.add_column("Input", justify="right", style=th.secondary, width=8)
    table.add_column("Cache", justify="right", style=f"bold {th.quota_high}", width=8)
    table.add_column("Output", justify="right", style=th.primary, width=8)
    table.add_column("Reason", justify="right", style=f"bold {th.quota_mid}", width=8)
    table.add_column("Total", justify="right", style="bold white", width=9)
    table.add_column("Cost", justify="right", style=f"bold {th.quota_high}", width=9)

    for idx, c in enumerate(report.top_conversations, 1):
        u = c.usage
        table.add_row(
            str(idx),
            c.title[:38] + "..." if len(c.title) > 38 else c.title,
            format_tokens(u.input_tokens),
            format_tokens(u.cache_read_tokens),
            format_tokens(u.output_tokens),
            format_tokens(u.reasoning_tokens),
            format_tokens(u.total_tokens),
            format_cost(u.cost_usd),
        )

    return table


def render_model_breakdown_table(models: list) -> Table:
    """Build a table showing token usage and estimated cost grouped by AI model."""
    th = get_theme_manager().get_active_theme()
    table = Table(
        title=f"[{th.title_style}]Token Usage & Estimated Cost by Model[/{th.title_style}]",
        box=DEFAULT_BOX,
        header_style=th.header_style,
        title_justify="left",
    )
    table.add_column("Model Group", style="bold white", min_width=28)
    table.add_column("Input", justify="right", style=th.secondary, width=9)
    table.add_column("Cache", justify="right", style=f"bold {th.quota_high}", width=9)
    table.add_column("Output", justify="right", style=th.primary, width=9)
    table.add_column("Reason", justify="right", style=f"bold {th.quota_mid}", width=9)
    table.add_column("Total Tokens", justify="right", style="bold white", width=12)
    table.add_column("Est. Cost", justify="right", style=f"bold {th.quota_high}", width=10)

    for m in models:
        u = m.usage
        table.add_row(
            m.display_name,
            format_tokens(u.input_tokens),
            format_tokens(u.cache_read_tokens),
            format_tokens(u.output_tokens),
            format_tokens(u.reasoning_tokens),
            format_tokens(u.total_tokens),
            format_cost(u.cost_usd),
        )
    return table
