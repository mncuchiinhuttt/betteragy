"""Tests for MCPRegistrar configuration manager."""

import json
from pathlib import Path
import pytest
from betteragy.mcp.mcp_registrar import MCPRegistrar


def test_mcp_registrar_lifecycle(tmp_path: Path) -> None:
    config_file = tmp_path / "mcp_config.json"
    settings_file = tmp_path / "settings.json"

    registrar = MCPRegistrar(config_paths=[config_file, settings_file])

    assert registrar.status()["registered"] is False

    entry = registrar.install(python_path="/custom/python3")
    assert entry["command"] == "/custom/python3"
    assert registrar.status()["registered"] is True

    # Verify JSON content
    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert "betteragy-todo" in data["mcpServers"]
    assert data["mcpServers"]["betteragy-todo"]["command"] == "/custom/python3"

    # Uninstall
    ok = registrar.uninstall()
    assert ok is True
    assert registrar.status()["registered"] is False
