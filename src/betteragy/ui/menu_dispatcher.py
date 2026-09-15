"""Main menu action dispatcher for Betteragy TUI."""

from .theme_manager import get_theme_manager


def dispatch_main_menu_action(tui, action: str) -> bool:
    """Dispatch enter key action on selected main menu item. Returns True to exit."""
    tui.status_message = ""
    if "Switch" in action:
        tui.current_screen, tui.account_idx = "switch_account", 0
    elif "Add" in action:
        tui.current_screen, tui.add_idx = "add_account", 0
    elif "Remove" in action:
        accounts = tui.acc_svc.get_accounts()
        if not accounts:
            tui.status_message = "[yellow]No accounts in pool to remove.[/yellow]"
        else:
            tui.current_screen, tui.account_idx = "remove_account", 0
    elif "Quota" in action or "Live" in action:
        tui.cached_quota, tui.current_screen = None, "quota"
    elif "Token" in action or "Usage" in action:
        tui.cached_report, tui.current_screen = None, "usage"
    elif "Rotate" in action:
        ok, msg = tui.rot_svc.rotate()
        tui.status_message = f"[bold green][ok] {msg}[/bold green]" if ok else f"[red][x] {msg}[/red]"
    elif "Set Cooldown" in action:
        ok, msg = tui.rot_svc.set_cooldown(hours=4.0)
        tui.status_message = f"[yellow]{msg}[/yellow]"
    elif "Tasks" in action:
        tui.current_screen = "tasks"
    elif "Harness" in action:
        tui.current_screen = "harness"
    elif "Proxy" in action:
        tui.current_screen = "proxy"
    elif "Theme" in action:
        tui.current_screen = "theme"
        mgr = get_theme_manager()
        themes = mgr.list_themes()
        active_id = mgr.get_active_theme_id()
        tui.theme_idx = next((i for i, th in enumerate(themes) if th.id == active_id), 0)
    elif "Shell" in action:
        tui.current_screen = "shell"
    elif "Update" in action:
        info = tui.update_svc.check_for_updates(force=True)
        if info and info.is_newer:
            tui.update_ver = info.latest_version
            tui.status_message = f"[bold yellow][!] Update available: v{info.latest_version}[/bold yellow]"
        elif info:
            tui.status_message = f"[bold green][ok] Betteragy is up to date (v{info.current_version})[/bold green]"
        else:
            tui.status_message = "[yellow][!] Could not check for updates (offline)[/yellow]"
    elif "Exit" in action:
        return True
    return False
