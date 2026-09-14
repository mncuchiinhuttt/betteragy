"""Stdio JSON-RPC 2.0 server entrypoint for Betteragy MCP To-Do engine."""

import json
import sys
from typing import Any, Dict

from betteragy.mcp.protocol import make_error_response, make_success_response, parse_request
from betteragy.mcp.task_db import TaskDB
from betteragy.mcp.todo_tools import TOOL_DEFINITIONS, execute_tool


class TodoServer:
    """MCP stdio server handling JSON-RPC requests."""

    def __init__(self, db: TaskDB | None = None) -> None:
        self.db = db or TaskDB()
        self.session_id: int | None = None

    def handle_request(self, req: Dict[str, Any]) -> Dict[str, Any] | None:
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}

        # Notifications without id do not require a response in JSON-RPC 2.0
        if req_id is None:
            return None

        if method == "server/discover":
            return make_success_response(
                req_id,
                {
                    "supportedVersions": ["2026-07-28", "2025-11-25", "2024-11-05"],
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "betteragy-todo", "version": "0.2.0"},
                    "instructions": "Betteragy To-Do execution engine for deterministic task tracking.",
                },
            )
        elif method == "initialize":
            client_version = params.get("protocolVersion", "2025-11-25")
            return make_success_response(
                req_id,
                {
                    "protocolVersion": client_version,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "betteragy-todo", "version": "0.2.0"},
                    "instructions": "Betteragy To-Do execution engine for deterministic task tracking.",
                },
            )
        elif method == "tools/list":
            return make_success_response(req_id, {"tools": TOOL_DEFINITIONS})
        elif method == "prompts/list":
            return make_success_response(req_id, {"prompts": []})
        elif method == "resources/list":
            return make_success_response(req_id, {"resources": []})
        elif method == "resources/templates/list":
            return make_success_response(req_id, {"resourceTemplates": []})
        elif method == "tools/call":
            name = params.get("name", "")
            args = params.get("arguments") or {}
            if self.session_id is not None and "session_id" not in args:
                args = dict(args)
                args["session_id"] = self.session_id
            try:
                result = execute_tool(name, args, self.db)
                if name == "todo_init" and "session_id" in result:
                    self.session_id = result["session_id"]
                return make_success_response(req_id, result)
            except Exception as exc:
                return make_error_response(req_id, -32603, f"Tool execution failed: {str(exc)}")
        elif method == "ping":
            return make_success_response(req_id, {})
        else:
            return make_error_response(req_id, -32601, f"Method not found: {method}")

    @staticmethod
    def _log(msg: str) -> None:
        try:
            with open("/tmp/betteragy_mcp.log", "a", encoding="utf-8") as f:
                f.write(msg)
        except OSError:
            pass

    def run(self) -> None:
        """Run standard I/O event loop."""
        self._log("--- Server started ---\n")
        for line in sys.stdin:
            self._log(f"IN: {line}")
            req, err = parse_request(line)
            if err:
                self._log(f"ERR: {json.dumps(err)}\n")
                sys.stdout.write(json.dumps(err) + "\n")
                sys.stdout.flush()
                continue
            if not req:
                continue

            resp = self.handle_request(req)
            if resp:
                self._log(f"OUT: {json.dumps(resp)}\n")
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()



def main() -> None:
    server = TodoServer()
    server.run()


if __name__ == "__main__":
    main()
