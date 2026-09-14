"""JSON-RPC 2.0 protocol formatting and parsing for MCP stdio servers."""

import json
from typing import Any, Dict, Optional, Tuple


def parse_request(raw_line: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Parse incoming JSON-RPC 2.0 message."""
    raw_line = raw_line.strip()
    if not raw_line:
        return None, None
    try:
        data = json.loads(raw_line)
        if not isinstance(data, dict):
            return None, make_error_response(None, -32600, "Invalid Request: not an object")
        return data, None
    except json.JSONDecodeError as exc:
        return None, make_error_response(None, -32700, f"Parse error: {str(exc)}")


def make_success_response(req_id: Any, result: Any) -> Dict[str, Any]:
    """Construct standard JSON-RPC 2.0 success response."""
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": result,
    }


def make_error_response(req_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    """Construct standard JSON-RPC 2.0 error response."""
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": err,
    }
