"""Unit tests for Betteragy Proxy shell auto-configuration."""

from pathlib import Path
from unittest.mock import patch

from betteragy.proxy.auto_config import (
    END_MARKER,
    START_MARKER,
    build_shell_block,
    install_auto_config,
    is_auto_config_installed,
    remove_auto_config,
)


def test_build_shell_block():
    """Verify generated shell block contains host, port, and functions."""
    block = build_shell_block("127.0.0.1", 45124)
    assert START_MARKER in block
    assert END_MARKER in block
    assert 'HTTPS_PROXY="http://127.0.0.1:45124"' in block
    assert 'SSL_CERT_FILE="$HOME/.config/betteragy/certs/ca_bundle.crt"' in block
    assert "agy()" in block
    assert "antigravity()" in block


def test_install_and_remove_auto_config(tmp_path: Path):
    """Test installing into rc file, checking presence, and cleanly removing."""
    fake_zshrc = tmp_path / ".zshrc"
    fake_zshrc.write_text('export FOO="bar"\nalias ll="ls -la"\n', encoding="utf-8")

    with patch("betteragy.proxy.auto_config._get_target_rc_files", return_value=[fake_zshrc]):
        # Initially not installed
        assert not is_auto_config_installed()

        # Install
        assert install_auto_config("127.0.0.1", 45124)
        assert is_auto_config_installed()
        content = fake_zshrc.read_text(encoding="utf-8")
        assert 'export FOO="bar"' in content
        assert START_MARKER in content
        assert 'http://127.0.0.1:45124' in content

        # Re-install (idempotent update)
        assert install_auto_config("127.0.0.1", 45124)
        content_after_reinstall = fake_zshrc.read_text(encoding="utf-8")
        assert content_after_reinstall.count(START_MARKER) == 1

        # Remove / Revert
        assert remove_auto_config()
        assert not is_auto_config_installed()
        cleaned_content = fake_zshrc.read_text(encoding="utf-8")
        assert START_MARKER not in cleaned_content
        assert 'export FOO="bar"' in cleaned_content
        assert 'alias ll="ls -la"' in cleaned_content
