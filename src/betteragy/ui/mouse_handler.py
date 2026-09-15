"""Precise mouse click and scroll event dispatcher for InteractiveTUI screens."""

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

    # Determine console width
    raw_w = getattr(getattr(tui, "console", None), "width", 100)
    c_width = raw_w if isinstance(raw_w, int) else 100
    is_wide_2col = c_width >= 150

    # 1. Main Menu Screen
    if screen == "main":
        menu_start_y = 4 + offset
        menu_end_y = menu_start_y + len(MAIN_MENU_ITEMS) - 1

        # Check if click is on left menu column
        is_menu_col = (x <= 75) if is_wide_2col else True

        if is_menu_col and menu_start_y <= y <= menu_end_y:
            clicked_idx = y - menu_start_y
            if 0 <= clicked_idx < len(MAIN_MENU_ITEMS):
                tui.menu_idx = clicked_idx
                tui.status_message = ""
                action = MAIN_MENU_ITEMS[clicked_idx][0]
                return tui._dispatch_action(action)

        # Right column shortcut clicks on wide screens (side-by-side)
        if is_wide_2col and x > 75:
            # Overview panel rows (Auto-rotate at line 5-6, Theme at line 7)
            if y in (5 + offset, 6 + offset):
                tui.current_screen = "proxy"
                return False
            if y == 7 + offset:
                return tui._dispatch_action("Theme")
            # Quota panel rows
            if 11 + offset <= y <= 15 + offset:
                return tui._dispatch_action("Quota")

        # Stacked layout on standard screens (< 150 cols)
        if not is_wide_2col:
            # Overview Card
            if y in (18 + offset, 21 + offset, 22 + offset):
                tui.current_screen = "proxy"
                return False
            if y == 23 + offset:
                return tui._dispatch_action("Theme")
            # Quota Card
            if 26 + offset <= y <= 29 + offset:
                return tui._dispatch_action("Quota")
            # Footer hint: click Exit
            if y >= 30 + offset:
                if x >= c_width - 15 or "Exit" in MAIN_MENU_ITEMS[tui.menu_idx][0]:
                    return True

        return False

    # 2. Account List Screens (Switch or Remove)
    if screen in ("switch_account", "remove_account"):
        accounts = tui.acc_svc.get_accounts()
        # Account 0 starts at line 5 + offset
        table_start_y = 5 + offset
        table_end_y = table_start_y + len(accounts) - 1

        if table_start_y <= y <= table_end_y:
            idx = y - table_start_y
            if 0 <= idx < len(accounts):
                tui.account_idx = idx
                from .account_flows import handle_account_list_key
                return handle_account_list_key(tui, KEY_ENTER)

        # Click on Back / Footer hints
        if y > table_end_y:
            tui.current_screen = "main"
            tui.status_message = ""
            return False

    # 3. Theme Selector Screen
    if screen == "theme":
        from .theme_manager import get_theme_manager
        themes = get_theme_manager().list_themes()
        table_start_y = 5 + offset
        table_end_y = table_start_y + len(themes) - 1
        if table_start_y <= y <= table_end_y:
            tui.theme_idx = y - table_start_y
            from .theme_flows import handle_theme_key
            return handle_theme_key(tui, KEY_ENTER)
        if y > table_end_y:
            tui.current_screen = "main"
            tui.status_message = ""
            return False
    # 4. Add Account Screen
    if screen == "add_account":
        m_start = 2 + offset
        if y in (m_start, m_start + 1):
            tui.add_idx = y - m_start
            from .account_flows import handle_add_account_key
            handle_add_account_key(tui, KEY_ENTER)
        elif y > m_start + 1:
            tui.current_screen = "main"
        return False

    # 5. Tasks Board Screen
    if screen == "tasks":
        from .session_flows import handle_tasks_key
        if y in (2 + offset, 3 + offset):
            handle_tasks_key(tui, "RIGHT")
            return False
        hdr_line = getattr(tui, "_task_header_line", None) or (9 + offset)
        tasks = getattr(tui, "_cached_tasks", None)
        if tasks is None:
            cur_id = getattr(tui, "selected_session_id", None)
            tasks = tui.task_db.get_tasks(session_id=cur_id) if cur_id else []
        start_y = hdr_line + 1
        end_y = start_y + len(tasks) - 1
        if tasks and start_y <= y <= end_y:
            tui.task_idx = y - start_y
            handle_tasks_key(tui, " ")
            return False
        if y > end_y:
            if x < 45:
                handle_tasks_key(tui, "c")
            else:
                tui.current_screen = "main"
            return False

    if screen == "proxy":
        from .proxy_flows import handle_proxy_key
        if y in (4 + offset, 17 + offset, 20 + offset):
            return handle_proxy_key(tui, "p")
        tui.current_screen = "main"
        return False

    # 7. Other screens: click to return to main
    tui.current_screen = "main"
    tui.status_message = ""
    return False


def handle_mouse_hover(tui, x: int, y: int) -> bool:
    """Update selection cursor on mouse hover. Returns True if selection changed."""
    screen = tui.current_screen
    offset = 3 if bool(tui.status_message) else 0
    raw_w = getattr(getattr(tui, "console", None), "width", 100)
    is_wide_2col = (raw_w if isinstance(raw_w, int) else 100) >= 150

    if screen == "main":
        start_y = 4 + offset
        if ((x <= 75) if is_wide_2col else True) and start_y <= y < start_y + len(MAIN_MENU_ITEMS):
            idx = y - start_y
            if idx != tui.menu_idx:
                tui.menu_idx = idx
                return True
        return False

    if screen in ("switch_account", "remove_account"):
        start_y = 5 + offset
        accs = tui.acc_svc.get_accounts()
        if start_y <= y < start_y + len(accs) and (y - start_y) != tui.account_idx:
            tui.account_idx = y - start_y
            return True
        return False

    if screen == "theme":
        from .theme_manager import get_theme_manager
        themes = get_theme_manager().list_themes()
        start_y = 5 + offset
        if start_y <= y < start_y + len(themes) and (y - start_y) != getattr(tui, "theme_idx", 0):
            tui.theme_idx = y - start_y
            return True
        return False

    if screen == "tasks":
        hdr_line = getattr(tui, "_task_header_line", None) or (9 + offset)
        tasks = getattr(tui, "_cached_tasks", None)
        if tasks is None:
            cur_id = getattr(tui, "selected_session_id", None)
            tasks = tui.task_db.get_tasks(session_id=cur_id) if cur_id else []
        start_y = hdr_line + 1
        if tasks and start_y <= y < start_y + len(tasks) and (y - start_y) != getattr(tui, "task_idx", 0):
            tui.task_idx = y - start_y
            return True
        return False

    if screen == "add_account" and y in (2 + offset, 3 + offset) and (y - (2 + offset)) != tui.add_idx:
        tui.add_idx = y - (2 + offset)
        return True

    return False
