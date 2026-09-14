"""Unit tests for UpdateService and semver comparison."""

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

from betteragy import __version__
from betteragy.services.update_service import UpdateService, parse_semver
from betteragy.ui.interactive_screens import MAIN_MENU_ITEMS
from betteragy.ui.interactive_tui import InteractiveTUI


def test_parse_semver():
    """Verify semantic version parsing and ordering."""
    assert parse_semver("v1.1.0") == (1, 1, 0)
    assert parse_semver("1.2.3") == (1, 2, 3)
    assert parse_semver("v2.0") == (2, 0, 0)
    assert parse_semver("invalid") == (0, 0, 0)
    assert parse_semver("v1.2.0") > parse_semver("1.1.9")
    assert parse_semver("2.0.0") > parse_semver("1.99.99")


def test_cache_write_and_read(tmp_path):
    """Verify cache writing and expiration checking."""
    cache_file = tmp_path / "update_cache.json"
    svc = UpdateService(cache_path=cache_file)

    # Empty cache
    assert svc._read_cache() is None

    # Write cache
    svc._write_cache("1.5.0", "https://github.com/release/v1.5.0")
    assert cache_file.exists()

    cached = svc._read_cache()
    assert cached is not None
    assert cached["latest_version"] == "1.5.0"
    assert cached["release_url"] == "https://github.com/release/v1.5.0"


def test_check_for_updates_cache_hit(tmp_path):
    """Verify cached update is returned without network calls."""
    cache_file = tmp_path / "update_cache.json"
    svc = UpdateService(cache_path=cache_file)
    svc._write_cache("99.0.0", "https://github.com/mock")

    info = svc.check_for_updates(force=False)
    assert info is not None
    assert info.latest_version == "99.0.0"
    assert info.is_newer is True
    assert info.current_version == __version__


def test_check_for_updates_mock_release(tmp_path):
    """Verify GitHub Releases API parsing when newer version available."""
    cache_file = tmp_path / "update_cache.json"
    svc = UpdateService(cache_path=cache_file)

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "tag_name": "v99.1.0",
        "html_url": "https://github.com/mock/releases/tag/v99.1.0"
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        info = svc.check_for_updates(force=True)
        assert info is not None
        assert info.latest_version == "99.1.0"
        assert info.is_newer is True
        assert "99.1.0" in info.release_url


def test_check_for_updates_offline_fallback(tmp_path):
    """Verify graceful fallback when network request fails."""
    cache_file = tmp_path / "update_cache.json"
    svc = UpdateService(cache_path=cache_file)

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("No route to host")):
        info = svc.check_for_updates(force=True)
        assert info is not None
        assert info.latest_version == __version__
        assert info.is_newer is False


def test_tui_updates_menu_dispatch(tmp_path):
    """Verify TUI dispatches check for updates and updates status message."""
    tui = InteractiveTUI()
    tui.update_svc = UpdateService(cache_path=tmp_path / "cache.json")

    # Mock an update available
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({"tag_name": "v9.0.0", "html_url": "https://example.com"}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        should_exit = tui._dispatch_action("Check for Updates")
        assert should_exit is False
        assert tui.update_ver == "9.0.0"
        assert "Update available" in tui.status_message
