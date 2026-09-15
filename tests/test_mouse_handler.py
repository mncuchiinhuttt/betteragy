"""Unit tests for mouse tracking sequence parser and TUI mouse click dispatcher."""

from unittest.mock import MagicMock
from betteragy.core.models import AccountRecord
from betteragy.ui.key_listener import KEY_DOWN, KEY_UP, KeyListener
from betteragy.ui.mouse_handler import handle_mouse_click, handle_mouse_hover


def test_mouse_sgr_sequence_parsing():
    """Verify KeyListener converts raw ANSI SGR sequences into key/click events."""
    # Left click press at col 15, row 8 -> CLICK:15:8
    assert KeyListener._parse_unix_sequence(b"\x1b[<0;15;8M") == "CLICK:15:8"
    # Left click release -> None
    assert KeyListener._parse_unix_sequence(b"\x1b[<0;15;8m") is None
    # Wheel up (b=64) -> KEY_UP
    assert KeyListener._parse_unix_sequence(b"\x1b[<64;10;5M") == KEY_UP
    # Wheel down (b=65) -> KEY_DOWN
    assert KeyListener._parse_unix_sequence(b"\x1b[<65;10;5M") == KEY_DOWN
    # Mouse motion / hover (b=35) -> HOVER:20:8
    assert KeyListener._parse_unix_sequence(b"\x1b[<35;20;8M") == "HOVER:20:8"
    # Multi-sequence buffer takes latest -> HOVER:10:9
    assert KeyListener._parse_unix_sequence(b"\x1b[<35;10;5M\x1b[<35;10;9M") == "HOVER:10:9"

def test_mouse_click_main_menu():
    """Verify clicking menu rows triggers item selection and action dispatch."""
    mock_tui = MagicMock()
    mock_tui.current_screen = "main"
    mock_tui.status_message = ""
    mock_tui.console.width = 100
    mock_tui._dispatch_action.return_value = False

    # Row 4 corresponds to Item 0 ([1] Switch Account)
    handle_mouse_click(mock_tui, 10, 4)
    assert mock_tui.menu_idx == 0
    assert mock_tui._dispatch_action.called

    # Row 5 corresponds to Item 1 ([2] Live AI Quotas)
    mock_tui._dispatch_action.reset_mock()
    handle_mouse_click(mock_tui, 10, 5)
    assert mock_tui.menu_idx == 1
    assert mock_tui._dispatch_action.called


def test_mouse_click_account_list():
    """Verify clicking account table row selects and switches account."""
    mock_tui = MagicMock()
    mock_tui.current_screen = "switch_account"
    mock_tui.status_message = ""
    mock_tui.acc_svc.switch_account.return_value = (True, "Switched")
    mock_tui.acc_svc.get_accounts.return_value = [
        AccountRecord(email="acc1@gmail.com", refresh_token="rf1"),
        AccountRecord(email="acc2@gmail.com", refresh_token="rf2"),
    ]
    # Row 5 corresponds to Account 0
    handle_mouse_click(mock_tui, 12, 5)
    mock_tui.acc_svc.switch_account.assert_called_with("acc1@gmail.com")

    # Reset screen and status_message; row 6 corresponds to Account 1
    mock_tui.current_screen = "switch_account"
    mock_tui.status_message = ""
    handle_mouse_click(mock_tui, 12, 6)
    mock_tui.acc_svc.switch_account.assert_called_with("acc2@gmail.com")


def test_mouse_hover_tracking():
    """Verify mouse hover moves selection cursor in real time."""
    mock_tui = MagicMock()
    mock_tui.current_screen = "main"
    mock_tui.status_message = ""
    mock_tui.menu_idx = 0
    mock_tui.console.width = 100

    # Hover over Row 5 (Item 1) -> changes index from 0 to 1, returns True (redraw)
    assert handle_mouse_hover(mock_tui, 15, 5) is True
    assert mock_tui.menu_idx == 1

    # Hover again over Row 5 -> index already 1, returns False (no unnecessary redraw)
    assert handle_mouse_hover(mock_tui, 25, 5) is False
    assert mock_tui.menu_idx == 1

    # Hover over Row 6 (Item 2) -> changes index to 2
    assert handle_mouse_hover(mock_tui, 15, 6) is True
    assert mock_tui.menu_idx == 2

def test_mouse_hover_and_click_theme():
    """Verify mouse hover and click on theme catalog."""
    from unittest.mock import patch
    mock_tui = MagicMock()
    mock_tui.current_screen = "theme"
    mock_tui.status_message = ""
    mock_tui.theme_idx = 0

    # Hover over line 6 (Theme 1: Emerald Forest)
    assert handle_mouse_hover(mock_tui, 15, 6) is True
    assert mock_tui.theme_idx == 1

    with patch("betteragy.ui.theme_manager.ThemeManager.set_active_theme") as mock_set:
        mock_set.return_value = True
        handle_mouse_click(mock_tui, 15, 6)
        assert mock_tui.current_screen == "main"
        assert mock_set.called
def test_mouse_tasks_hover_and_clear():
    """Verify mouse hover over tasks and clear tasks button."""
    mock_tui = MagicMock()
    mock_tui.current_screen = "tasks"
    mock_tui.status_message = ""
    mock_tui.task_idx = 0
    mock_tui.selected_session_id = 1
    mock_tui._task_header_line = 9
    mock_tui.task_db.list_sessions.return_value = [{"id": 1}]
    tasks = [
        {"id": 10, "title": "Task 1", "status": "pending", "priority": "high"},
        {"id": 11, "title": "Task 2", "status": "in_progress", "priority": "medium"},
    ]
    mock_tui.task_db.get_tasks.return_value = tasks
    mock_tui._cached_tasks = tasks
    mock_tui.task_db.clear_tasks.return_value = 2
    # Hover over line 11 (Task 1)
    assert handle_mouse_hover(mock_tui, 15, 11) is True
    assert mock_tui.task_idx == 1

    # Click clear tasks button at line 21
    handle_mouse_click(mock_tui, 20, 21)
    assert "Cleared 2 task(s)" in mock_tui.status_message
