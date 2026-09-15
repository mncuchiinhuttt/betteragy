"""View composition and rendering helper for InteractiveTUI screens."""

from rich.panel import Panel
from rich.syntax import Syntax

from ..commands.shell_cmd import SHELL_SNIPPET
from .cards import render_kpi_cards
from .dashboard_cards import render_active_overview_card, render_mini_quota_card
from .interactive_screens import (
    render_account_selector_panel,
    render_add_account_panel,
    render_footer_hints,
    render_main_menu_panel,
    render_oauth_waiting_panel,
)
from .tables import render_quota_table, render_top_conversations_table
from .theme import DEFAULT_BOX
from .theme_manager import get_theme_manager


def build_screen_elements(tui) -> list:
    """Compose the visual elements for the active TUI screen."""
    elements = []
    if tui.status_message:
        elements.append(Panel(tui.status_message, style="bold green", box=DEFAULT_BOX))

    active_acc = tui.acc_svc.get_active_account()
    active_email = active_acc.email if active_acc else "None"
    accounts = tui.acc_svc.get_accounts()

    if tui.current_screen == "main":
        update_ver = getattr(tui, "update_ver", None)
        proxy_active = getattr(tui, "_is_proxy_active", lambda: False)()
        theme_name = get_theme_manager().get_active_theme_id()

        menu_panel = render_main_menu_panel(
            tui.menu_idx, active_email, update_ver=update_ver, proxy_active=proxy_active
        )
        overview_card = render_active_overview_card(
            active_acc, proxy_active, theme_name, len(accounts), update_ver=update_ver
        )
        quota_card = render_mini_quota_card(getattr(tui, "cached_quota", None))

        from rich.columns import Columns
        from rich.console import Group
        c_width = getattr(getattr(tui, "console", None), "width", 100) or 100
        if c_width >= 95:
            right_col = Group(overview_card, quota_card)
            body = Columns([menu_panel, right_col], equal=False, expand=True)
            elements.extend([body, render_footer_hints("main")])
        else:
            elements.extend([menu_panel, overview_card, quota_card, render_footer_hints("main")])
    elif tui.current_screen == "switch_account":
        elements.extend([render_account_selector_panel(accounts, tui.account_idx, active_email), render_footer_hints("sub")])
    elif tui.current_screen == "remove_account":
        p = render_account_selector_panel(accounts, tui.account_idx, active_email, "-- Select Account to Remove --", "Remove Selected")
        elements.extend([p, render_footer_hints("sub")])
    elif tui.current_screen == "add_account":
        elements.extend([render_add_account_panel(tui.add_idx), render_footer_hints("sub")])
    elif tui.current_screen == "oauth_waiting":
        elements.extend([render_oauth_waiting_panel(), render_footer_hints("oauth")])
    elif tui.current_screen == "quota":
        if not tui.cached_quota and active_acc:
            fetch_fn = getattr(tui, "_fetch_active_quota", None)
            tui.cached_quota = fetch_fn(active_acc.email) if fetch_fn else tui.quota_agg.fetch_single_account(active_acc.email)
        elements.append(render_quota_table(tui.cached_quota) if tui.cached_quota else Panel("[yellow]No quota data available.[/yellow]", box=DEFAULT_BOX))
        elements.append(render_footer_hints("sub"))
    elif tui.current_screen == "usage":
        if not tui.cached_report:
            tui.cached_report = tui.usage_agg.get_report(period="all")
        elements.append(render_kpi_cards(tui.cached_report, active_acc))
        if tui.cached_report.top_conversations:
            elements.append(render_top_conversations_table(tui.cached_report))
        elements.append(render_footer_hints("sub"))
    elif tui.current_screen == "shell":
        syntax = Syntax(SHELL_SNIPPET, "bash", theme="monokai", line_numbers=False)
        elements.extend([Panel(syntax, title="[bold cyan]>> Shell Integration[/bold cyan]", box=DEFAULT_BOX), render_footer_hints("sub")])
    elif tui.current_screen == "tasks":
        from .task_renderer import render_ascii_task_board
        sess_id = getattr(tui, "selected_session_id", None)
        elements.extend([render_ascii_task_board(tui.task_db, session_id=sess_id), render_footer_hints("tasks")])
    elif tui.current_screen == "session_selector":
        from .session_flows import render_session_selector_panel
        sessions = tui.task_db.list_sessions(limit=20)
        elements.extend([render_session_selector_panel(sessions, tui.session_idx), render_footer_hints("session_selector")])
    elif tui.current_screen == "harness":
        from ..harness.harness_service import HarnessService
        stat = HarnessService().status()
        if stat["installed"]:
            body = (
                f"[bold green][ok] Harness is active[/bold green]\n\n"
                f"[dim]Profile:[/] [cyan]{stat['profile']}[/cyan]\n"
                f"[dim]Location:[/] [yellow]{stat['path']}[/yellow]\n"
                f"[dim]Size:[/] {stat['size_bytes']} bytes\n\n"
                f"[dim]Directives enforce deep reasoning, falsification, and To-Do planning.[/dim]"
            )
        else:
            body = (
                "[bold yellow][!] Harness is not installed[/bold yellow]\n\n"
                "[dim]To install and activate in agy, run:[/] [cyan]betteragy harness install[/cyan]"
            )
        elements.extend([Panel(body, title="[~] Betteragy Reasoning Harness", box=DEFAULT_BOX), render_footer_hints("sub")])
    elif tui.current_screen == "proxy":
        from .proxy_flows import render_proxy_panel
        elements.extend([render_proxy_panel(tui), render_footer_hints("proxy")])
    elif tui.current_screen == "theme":
        from .theme_flows import render_theme_selector_panel
        mgr = get_theme_manager()
        themes = mgr.list_themes()
        active_id = mgr.get_active_theme_id()
        elements.extend([render_theme_selector_panel(themes, getattr(tui, "theme_idx", 0), active_id), render_footer_hints("theme")])

    return elements

