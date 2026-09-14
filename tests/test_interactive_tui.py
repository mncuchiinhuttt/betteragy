"""Unit tests for KeyListener and InteractiveTUI navigation logic."""

import os
from unittest.mock import MagicMock

from betteragy.ui.account_flows import save_oauth_account
from betteragy.ui.interactive_screens import MAIN_MENU_ITEMS
from betteragy.ui.interactive_tui import InteractiveTUI
from betteragy.ui.key_listener import (
    KEY_BACK,
    KEY_DOWN,
    KEY_ENTER,
    KEY_ESC,
    KEY_LEFT,
    KEY_QUIT,
    KEY_RIGHT,
    KEY_UP,
    KeyListener,
)


def test_parse_unix_arrow_sequences():
    """Verify CSI and SS3 terminal sequences map correctly to arrows."""
    listener = KeyListener()
    assert listener._parse_unix_sequence(b"\x1b[A") == KEY_UP
    assert listener._parse_unix_sequence(b"\x1b[B") == KEY_DOWN
    assert listener._parse_unix_sequence(b"\x1b[C") == KEY_RIGHT
    assert listener._parse_unix_sequence(b"\x1b[D") == KEY_LEFT

    # Application cursor mode (SS3)
    assert listener._parse_unix_sequence(b"\x1bOA") == KEY_UP
    assert listener._parse_unix_sequence(b"\x1bOB") == KEY_DOWN
    assert listener._parse_unix_sequence(b"\x1bOC") == KEY_RIGHT
    assert listener._parse_unix_sequence(b"\x1bOD") == KEY_LEFT

    # Page Up / Page Down
    assert listener._parse_unix_sequence(b"\x1b[5~") == KEY_UP
    assert listener._parse_unix_sequence(b"\x1b[6~") == KEY_DOWN


def test_parse_unix_control_keys():
    """Verify Enter, Esc, Backspace, and shortcuts."""
    listener = KeyListener()
    assert listener._parse_unix_sequence(b"\x1b") == KEY_ESC
    assert listener._parse_unix_sequence(b"\r") == KEY_ENTER
    assert listener._parse_unix_sequence(b"\n") == KEY_ENTER
    assert listener._parse_unix_sequence(b"q") == KEY_QUIT
    assert listener._parse_unix_sequence(b"Q") == KEY_QUIT
    assert listener._parse_unix_sequence(b"j") == KEY_DOWN
    assert listener._parse_unix_sequence(b"k") == KEY_UP
    assert listener._parse_unix_sequence(b"\x7f") == KEY_BACK


def test_read_unix_pipe_down_arrow():
    """Verify that simulated down arrow bytes in pipe are read cleanly via os.read."""
    r_fd, w_fd = os.pipe()
    try:
        listener = KeyListener()
        listener.fd = r_fd

        os.write(w_fd, b"\x1b[B")
        key = listener._read_unix()
        assert key == KEY_DOWN
    finally:
        os.close(r_fd)
        os.close(w_fd)


def test_main_menu_down_arrow_does_not_exit():
    """Verify that pressing DOWN on main menu moves selection and DOES NOT exit."""
    tui = InteractiveTUI()
    tui.menu_idx = 0
    tui.status_message = "test"

    should_exit = tui._handle_main_key(KEY_DOWN)
    assert should_exit is False
    assert tui.menu_idx == 1
    assert tui.status_message == ""


def test_main_menu_up_arrow_wraps_around():
    """Verify UP arrow wraps around to last item without exiting."""
    tui = InteractiveTUI()
    tui.menu_idx = 0

    should_exit = tui._handle_main_key(KEY_UP)
    assert should_exit is False
    assert tui.menu_idx == len(MAIN_MENU_ITEMS) - 1


def test_main_menu_esc_does_not_exit():
    """Verify ESC on main menu clears status but does NOT exit."""
    tui = InteractiveTUI()
    tui.status_message = "Some message"

    should_exit = tui._handle_main_key(KEY_ESC)
    assert should_exit is False
    assert tui.status_message == ""


def test_main_menu_quit_key_exits():
    """Verify 'q' key exits application."""
    tui = InteractiveTUI()
    assert tui._handle_main_key(KEY_QUIT) is True


def test_main_menu_enter_transitions_screen():
    """Verify Enter on 'Switch Account' opens switch_account screen."""
    tui = InteractiveTUI()
    tui.menu_idx = 0  # Switch Account
    should_exit = tui._handle_main_key(KEY_ENTER)
    assert should_exit is False
    assert tui.current_screen == "switch_account"


def test_main_menu_enter_add_account():
    """Verify Enter on 'Add Account' opens add_account screen."""
    tui = InteractiveTUI()
    # Find Add Account index
    add_idx = next(i for i, item in enumerate(MAIN_MENU_ITEMS) if "Add Account" in item[0])
    tui.menu_idx = add_idx
    should_exit = tui._handle_main_key(KEY_ENTER)
    assert should_exit is False
    assert tui.current_screen == "add_account"


def test_account_list_screen_esc_returns_to_main():
    """Verify ESC on account list screen goes back to main screen."""
    tui = InteractiveTUI()
    tui.current_screen = "switch_account"
    tui._handle_account_list_key(KEY_ESC)
    assert tui.current_screen == "main"


def test_add_account_screen_esc_returns_to_main():
    """Verify ESC on add account screen goes back to main screen."""
    tui = InteractiveTUI()
    tui.current_screen = "add_account"
    tui._handle_add_account_key(KEY_ESC)
    assert tui.current_screen == "main"


def test_save_oauth_account():
    """Verify saving oauth tokens creates valid AccountRecord."""
    mock_acc_svc = MagicMock()
    oauth_res = {
        "tokens": {"refresh_token": "mock_rf", "access_token": "mock_at"},
        "user_info": {"email": "test@example.com", "name": "Tester"},
    }
    rec = save_oauth_account(mock_acc_svc, oauth_res)
    assert rec is not None
    assert rec.email == "test@example.com"
    mock_acc_svc.add_or_update_account.assert_called_once()
