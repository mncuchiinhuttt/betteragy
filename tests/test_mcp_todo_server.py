"""Tests for MCP To-Do JSON-RPC 2.0 stdio server and tools."""

import json
import pytest
from betteragy.mcp.protocol import make_error_response, make_success_response, parse_request
from betteragy.mcp.task_db import TaskDB
from betteragy.mcp.todo_server import TodoServer


def test_protocol_parsing_and_responses() -> None:
    req, err = parse_request('{"jsonrpc": "2.0", "id": 1, "method": "ping"}\n')
    assert err is None
    assert req["method"] == "ping"
    assert req["id"] == 1

    # Invalid JSON
    req, err = parse_request("{invalid_json\n")
    assert req is None
    assert err["error"]["code"] == -32700

    # Non-object JSON
    req, err = parse_request('"hello"\n')
    assert req is None
    assert err["error"]["code"] == -32600

    # Success and Error response builders
    succ = make_success_response(1, {"val": 42})
    assert succ["result"]["val"] == 42
    err_resp = make_error_response(2, -32601, "Not Found")
    assert err_resp["error"]["message"] == "Not Found"


def test_todo_server_dispatch() -> None:
    db = TaskDB(db_path=":memory:")
    server = TodoServer(db=db)

    # Initialize
    resp = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert "capabilities" in resp["result"]
    assert resp["result"]["serverInfo"]["name"] == "betteragy-todo"

    # Tools list
    resp = server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tool_names = [t["name"] for t in resp["result"]["tools"]]
    assert "todo_init" in tool_names
    assert "todo_add" in tool_names
    assert "todo_update" in tool_names
    assert "todo_list" in tool_names
    assert "todo_clear" in tool_names

    # Call todo_init
    resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "todo_init", "arguments": {"goal": "Test Goal"}},
    })
    assert "Initialized task session" in resp["result"]["content"][0]["text"]

    # Call todo_add
    resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "todo_add", "arguments": {"title": "Task A", "priority": "high"}},
    })
    assert "Added task" in resp["result"]["content"][0]["text"]

    # Call todo_update
    resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {"name": "todo_update", "arguments": {"task_id": 1, "status": "completed", "evidence": "Verified"}},
    })
    assert "Task #1 updated to 'completed'" in resp["result"]["content"][0]["text"]

    # Call todo_list
    resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {"name": "todo_list", "arguments": {}},
    })
    text = resp["result"]["content"][0]["text"]
    assert "Test Goal" in text
    assert "[x] #1 Task A" in text
    assert "|--" in text

    # Call unknown method
    resp = server.handle_request({"jsonrpc": "2.0", "id": 7, "method": "unknown"})
    assert resp["error"]["code"] == -32601


def test_todo_server_discover_and_features() -> None:
    server = TodoServer(db=TaskDB(db_path=":memory:"))

    # server/discover
    resp = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "server/discover"})
    assert "supportedVersions" in resp["result"]
    assert "capabilities" in resp["result"]
    assert "tools" in resp["result"]["capabilities"]

    # initialize echoing protocol version
    resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "initialize",
        "params": {"protocolVersion": "2025-11-25"},
    })
    assert resp["result"]["protocolVersion"] == "2025-11-25"

    # notifications without id
    assert server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    assert server.handle_request({"jsonrpc": "2.0", "method": "$/cancelRequest"}) is None

    # prompts and resources
    p_resp = server.handle_request({"jsonrpc": "2.0", "id": 3, "method": "prompts/list"})
    assert p_resp["result"]["prompts"] == []
    r_resp = server.handle_request({"jsonrpc": "2.0", "id": 4, "method": "resources/list"})
    assert r_resp["result"]["resources"] == []
    rt_resp = server.handle_request({"jsonrpc": "2.0", "id": 5, "method": "resources/templates/list"})
    assert rt_resp["result"]["resourceTemplates"] == []


def test_todo_server_session_affinity() -> None:
    """Verify separate TodoServer instances maintain distinct session bindings."""
    shared_db = TaskDB(db_path=":memory:")

    # Server 1 in terminal tab 1
    server1 = TodoServer(db=shared_db)
    resp1 = server1.handle_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "todo_init", "arguments": {"goal": "Tab 1 Work", "project_name": "repo1"}},
    })
    assert "session #" in resp1["result"]["content"][0]["text"].lower()
    s1_id = server1.session_id
    assert s1_id is not None

    # Server 2 in terminal tab 2
    server2 = TodoServer(db=shared_db)
    resp2 = server2.handle_request({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "todo_init", "arguments": {"goal": "Tab 2 Work", "project_name": "repo2"}},
    })
    s2_id = server2.session_id
    assert s2_id is not None
    assert s1_id != s2_id

    # Server 1 adds task without explicit session_id (should use self.session_id)
    server1.handle_request({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "todo_add", "arguments": {"title": "Tab 1 Task"}},
    })

    # Server 2 adds task without explicit session_id
    server2.handle_request({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "todo_add", "arguments": {"title": "Tab 2 Task"}},
    })

    # Listing on Server 1 only shows Tab 1 Task
    list1 = server1.handle_request({
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {"name": "todo_list", "arguments": {}},
    })
    text1 = list1["result"]["content"][0]["text"]
    assert "Tab 1 Task" in text1
    assert "Tab 2 Task" not in text1

    # Listing on Server 2 only shows Tab 2 Task
    list2 = server2.handle_request({
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {"name": "todo_list", "arguments": {}},
    })
    text2 = list2["result"]["content"][0]["text"]
    assert "Tab 2 Task" in text2
    assert "Tab 1 Task" not in text2


