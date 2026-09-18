"""Registrar for injecting Betteragy MCP server into agy settings."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_CONFIG_PATH = Path.home() / ".gemini" / "config" / "mcp_config.json"
DEFAULT_SETTINGS_PATH = Path.home() / ".gemini" / "settings.json"
SERVER_KEY = "betteragy-todo"


class MCPRegistrar:
    """Safely registers and unregisters MCP servers in agy config."""

    def __init__(self, config_paths: List[Path] | None = None) -> None:
        self.config_paths = config_paths or [DEFAULT_CONFIG_PATH, DEFAULT_SETTINGS_PATH]

    @property
    def settings_path(self) -> Path:
        return self.config_paths[0]


    @property
    def settings_path(self) -> str:
        """Primary settings path."""
        return str(self.config_paths[0])

    def _update_file(self, path: Path, updater: Any) -> bool:
        data = {"mcpServers": {}}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {"mcpServers": {}}
        if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
            data["mcpServers"] = {}

        modified = updater(data)
        if modified:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return modified

    def install(self, python_path: str | None = None) -> Dict[str, Any]:
        """Register betteragy-todo server in agy configs with reliable python binary."""
        import shutil
        uv_tool_py = Path.home() / ".local" / "share" / "uv" / "tools" / "betteragy" / "bin" / "python"
        py_exe = python_path or (str(uv_tool_py) if uv_tool_py.exists() else shutil.which("python3") or sys.executable)
        server_entry = {
            "command": py_exe,
            "args": ["-m", "betteragy.mcp.todo_server"],
            "disabled": False,
        }

        def add_server(data: Dict[str, Any]) -> bool:
            data["mcpServers"][SERVER_KEY] = dict(server_entry)
            return True

        for p in self.config_paths:
            self._update_file(p, add_server)

        return server_entry

    def uninstall(self) -> bool:
        """Remove betteragy-todo server from configs."""
        def remove_server(data: Dict[str, Any]) -> bool:
            if SERVER_KEY in data.get("mcpServers", {}):
                del data["mcpServers"][SERVER_KEY]
                return True
            return False

        any_removed = False
        for p in self.config_paths:
            if self._update_file(p, remove_server):
                any_removed = True
        return any_removed

    def status(self) -> Dict[str, Any]:
        """Check if betteragy-todo is registered."""
        for p in self.config_paths:
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    if SERVER_KEY in data.get("mcpServers", {}):
                        entry = data["mcpServers"][SERVER_KEY]
                        return {
                            "registered": True,
                            "settings_path": str(p),
                            "command": entry.get("command"),
                            "args": entry.get("args"),
                        }
                except (json.JSONDecodeError, OSError):
                    pass
        return {
            "registered": False,
            "settings_path": str(self.config_paths[0]),
            "command": None,
            "args": None,
        }

