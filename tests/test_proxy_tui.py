"""Unit tests for Proxy TUI panel, key handlers, and CLI commands."""

from unittest.mock import MagicMock, patch
from rich.console import Console
from typer.testing import CliRunner

from betteragy.cli import app
from betteragy.core.models import AccountRecord
from betteragy.ui.interactive_screens import MAIN_MENU_ITEMS
from betteragy.ui.interactive_tui import InteractiveTUI
from betteragy.ui.key_listener import KEY_ESC, KEY_QUIT, KEY_REFRESH
from betteragy.ui.proxy_flows import handle_proxy_key, render_proxy_panel

runner = CliRunner()


def _render_to_text(renderable) -> str:
    console = Console(record=True, width=120)
    console.print(renderable)
    return console.export_text()


def test_render_proxy_panel_stopped():
    """Verify render_proxy_panel renders stopped state with features list."""
    mock_tui = MagicMock()
    mock_tui.acc_svc.get_active_account.return_value = None

    with patch("betteragy.ui.proxy_flows.get_proxy_pid", return_value=None), \
         patch("betteragy.ui.proxy_flows.is_healthy", return_value=False):
        panel = render_proxy_panel(mock_tui)
        assert panel is not None
        rendered = _render_to_text(panel)
        assert "STOPPED" in rendered
        assert "Zero-Restart Switching" in rendered


def test_render_proxy_panel_running():
    """Verify render_proxy_panel renders active PID, active account, and instructions."""
    mock_tui = MagicMock()
    mock_acc = AccountRecord(email="pilot@gmail.com", refresh_token="rf_pilot")
    mock_tui.acc_svc.get_active_account.return_value = mock_acc

    with patch("betteragy.ui.proxy_flows.get_proxy_pid", return_value=98765), \
         patch("betteragy.ui.proxy_flows.is_healthy", return_value=True):
        panel = render_proxy_panel(mock_tui)
        rendered = _render_to_text(panel)
        assert "ACTIVE (PID: 98765)" in rendered
        assert "pilot@gmail.com" in rendered
        assert "HTTPS_PROXY" in rendered


def test_handle_proxy_key_navigation_and_toggle():
    """Verify proxy screen key handling for back, quit, and toggle."""
    mock_tui = MagicMock()
    mock_tui.current_screen = "proxy"
    mock_tui.status_message = "old"

    # ESC returns to main
    exit_app = handle_proxy_key(mock_tui, KEY_ESC)
    assert exit_app is False
    assert mock_tui.current_screen == "main"
    assert mock_tui.status_message == ""

    # 'q' exits application
    assert handle_proxy_key(mock_tui, KEY_QUIT) is True

    # 'r' refreshes status
    mock_tui.status_message = "some"
    assert handle_proxy_key(mock_tui, KEY_REFRESH) is False
    assert mock_tui.status_message == ""

    # 'p' toggles proxy daemon
    with patch("betteragy.ui.proxy_flows.is_proxy_running", return_value=False), \
         patch("betteragy.ui.proxy_flows.start_proxy_daemon", return_value=(True, 12345, "Started")):
        handle_proxy_key(mock_tui, "p")
        assert "12345" in mock_tui.status_message

    with patch("betteragy.ui.proxy_flows.is_proxy_running", return_value=True), \
         patch("betteragy.ui.proxy_flows.stop_proxy_daemon", return_value=True):
        handle_proxy_key(mock_tui, "p")
        assert "stopped" in mock_tui.status_message


def test_tui_main_menu_enter_proxy_screen():
    """Verify Enter on 'Zero-Restart Proxy' opens proxy screen."""
    tui = InteractiveTUI()
    proxy_idx = next(i for i, item in enumerate(MAIN_MENU_ITEMS) if "Zero-Restart Proxy" in item[0])
    tui.menu_idx = proxy_idx
    should_exit = tui._dispatch_action(MAIN_MENU_ITEMS[proxy_idx][0])
    assert should_exit is False
    assert tui.current_screen == "proxy"


def test_cli_proxy_status_and_help():
    """Verify CLI commands betteragy proxy --help and status."""
    res = runner.invoke(app, ["proxy", "--help"])
    assert res.exit_code == 0
    assert "start" in res.stdout
    assert "stop" in res.stdout
    assert "status" in res.stdout

    res_status = runner.invoke(app, ["proxy", "status"])
    assert res_status.exit_code == 0
    assert "Proxy" in res_status.stdout
