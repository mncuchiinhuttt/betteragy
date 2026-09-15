"""Mouse click and scroll event dispatcher for InteractiveTUI screens."""

from typing import Optional
from .interactive_screens import MAIN_MENU_ITEMS
from .key_listener import KEY_ENTER, KEY_ESC


def handle_mouse_click(tui, x: int, y: int) -> bool:
    """Dispatch mouse click coordinates (1-based x, y) to active screen actions.
    Returns True if the action signals application exit.
    """
    screen = tui.current_screen
    has_status = bool(tui.status_message)
    offset = 3 if has_status else 0

    # 1. Main Menu Screen
    if screen == "main":
        menu_start_y = 5 + offset
        menu_end_y = menu_start_y + len(MAIN_MENU_ITEMS) - 1
        raw_w = getattr(getattr(tui, "console", None), "width", 100)
        c_width = raw_w if isinstance(raw_w, int) else 100
        is_menu_col = x <= 65 or c_width < 95

        if is_menu_col and menu_start_y <= y <= menu_end_y:
            clicked_idx = y - menu_start_y
            if 0 <= clicked_idx < len(MAIN_MENU_ITEMS):
                tui.menu_idx = clicked_idx
                tui.status_message = ""
                action = MAIN_MENU_ITEMS[clicked_idx][0]
                return tui._dispatch_action(action)

        # Right column shortcut clicks on desktop
        if c_width >= 95 and x > 65:
            # Proxy shortcut or theme shortcut in right column
            if y in (menu_start_y + 1, menu_start_y + 2):
                tui.current_screen = "proxy"
                return False
            if y in (menu_start_y + 3, menu_start_y + 4):
                return tui._dispatch_action("Theme")

        return False

    # 2. Account List Screens (Switch or Remove)
    if screen in ("switch_account", "remove_account"):
        accounts = tui.acc_svc.get_accounts()
        table_start_y = 4 + offset
        table_end_y = table_start_y + len(accounts) - 1

        if table_start_y <= y <= table_end_y:
            idx = y - table_start_y
            if 0 <= idx < len(accounts):
                tui.account_idx = idx
                from .account_flows import handle_account_list_key
                return handle_account_list_key(tui, KEY_ENTER)

        # Click on back / exit hints
        if y > table_end_y:
            tui.current_screen = "main"
            tui.status_message = ""
            return False

    # 3. Theme Selector Screen
    if screen == "theme":
        from .theme_manager import get_theme_manager
        themes = get_theme_manager().list_themes()
        table_start_y = 4 + offset
        table_end_y = table_start_y + len(themes) - 1

        if table_start_y <= y <= table_end_y:
            idx = y - table_start_y
            if 0 <= idx < len(themes):
                tui.theme_idx = idx
                from .theme_flows import handle_theme_key
                return handle_theme_key(tui, KEY_ENTER)

        if y > table_end_y:
            tui.current_screen = "main"
            tui.status_message = ""
            return False

    # 4. Add Account Screen
    if screen == "add_account":
        m_start_y = 3 + offset
        if y == m_start_y:
            tui.add_idx = 0
            from .account_flows import handle_add_account_key
            handle_add_account_key(tui, KEY_ENTER)
            return False
        if y == m_start_y + 1:
            tui.add_idx = 1
            from .account_flows import handle_add_account_key
            handle_add_account_key(tui, KEY_ENTER)
            return False
        if y > m_start_y + 1:
            tui.current_screen = "main"
            return False

    # 5. Proxy Screen
    if screen == "proxy":
        from .proxy_flows import handle_proxy_key
        # Check toggle button click or back
        if 8 + offset <= y <= 12 + offset:
            return handle_proxy_key(tui, "p")
        if y >= 14 + offset:
            tui.current_screen = "main"
            return False

    # 6. Informational Screens (Quota, Usage, Shell, Harness, Tasks)
    if screen in ("quota", "usage", "shell", "harness", "tasks", "oauth_waiting"):
        tui.current_screen = "main"
        tui.status_message = ""
        return False

    return False
