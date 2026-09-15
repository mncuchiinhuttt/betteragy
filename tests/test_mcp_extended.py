"""Tests for extended Betteragy MCP tools: Quota, Checkpoints, and Delegation."""

from unittest.mock import MagicMock, patch
import pytest

from betteragy.core.models import AccountQuota, AccountRecord, AccountsStorage, QuotaBucket
from betteragy.mcp.checkpoint_db import CheckpointDB
from betteragy.mcp.task_db import TaskDB
from betteragy.mcp.todo_server import TodoServer


@pytest.fixture
def clean_server(tmp_path) -> TodoServer:
    db_file = tmp_path / "test_tasks.db"
    db = TaskDB(db_path=db_file)
    cp_db = CheckpointDB(db_path=db_file)
    return TodoServer(db=db, cp_db=cp_db)


def test_delegation_and_dependencies(clean_server: TodoServer) -> None:
    # 1. Init session
    resp = clean_server.handle_request({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "todo_init", "arguments": {"goal": "Multi-agent Project"}},
    })
    assert resp["result"]["session_id"] is not None

    # 2. Add Task 1 assigned to researcher
    resp = clean_server.handle_request({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {
            "name": "todo_add",
            "arguments": {"title": "Research API", "assigned_to": "researcher"},
        },
    })
    assert "@researcher" in resp["result"]["content"][0]["text"]

    # 3. Add Task 2 depending on Task 1, assigned to coder
    resp = clean_server.handle_request({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {
            "name": "todo_add",
            "arguments": {"title": "Implement Feature", "assigned_to": "coder", "depends_on": "1"},
        },
    })
    text = resp["result"]["content"][0]["text"]
    assert "@coder" in text
    assert "needs #1" in text
    assert "[!] Blocked by pending: #1" in text

    # 4. Complete Task 1 -> Task 2 unblocked
    clean_server.handle_request({
        "jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {"name": "todo_update", "arguments": {"task_id": 1, "status": "completed"}},
    })
    resp = clean_server.handle_request({
        "jsonrpc": "2.0", "id": 5, "method": "tools/call",
        "params": {"name": "todo_list", "arguments": {}},
    })
    text = resp["result"]["content"][0]["text"]
    assert "[!] Blocked by pending" not in text


def test_checkpoint_tools(clean_server: TodoServer) -> None:
    # Save checkpoint
    save_resp = clean_server.handle_request({
        "jsonrpc": "2.0", "id": 10, "method": "tools/call",
        "params": {
            "name": "checkpoint_save",
            "arguments": {
                "name": "step_01_done",
                "summary": "Completed DB migrations and schema setup.",
                "next_steps": "Begin implementing REST controllers.",
                "context_data": {"active_files": ["db.py", "schema.py"]},
            },
        },
    })
    assert "checkpoint_id" in save_resp["result"]
    assert "[ok] Saved checkpoint" in save_resp["result"]["content"][0]["text"]

    # List checkpoints
    list_resp = clean_server.handle_request({
        "jsonrpc": "2.0", "id": 11, "method": "tools/call",
        "params": {"name": "checkpoint_list", "arguments": {}},
    })
    assert "step_01_done" in list_resp["result"]["content"][0]["text"]

    # Resume checkpoint
    resume_resp = clean_server.handle_request({
        "jsonrpc": "2.0", "id": 12, "method": "tools/call",
        "params": {"name": "checkpoint_resume", "arguments": {"name": "step_01_done"}},
    })
    r_text = resume_resp["result"]["content"][0]["text"]
    assert "RESUMED CHECKPOINT" in r_text
    assert "Completed DB migrations" in r_text
    assert "Begin implementing REST controllers." in r_text


@patch("betteragy.mcp.quota_tools.AccountService")
@patch("betteragy.mcp.quota_tools.QuotaAggregator")
def test_quota_and_account_tools(mock_agg_cls, mock_acc_cls, clean_server: TodoServer) -> None:
    mock_acc_inst = MagicMock()
    mock_acc_cls.return_value = mock_acc_inst
    acc1 = AccountRecord(email="user1@example.com", refresh_token="tok1", tier_name="Standard")
    acc2 = AccountRecord(email="user2@example.com", refresh_token="tok2", tier_name="Enterprise")
    mock_acc_inst.get_accounts.return_value = [acc1, acc2]
    mock_acc_inst.get_active_account.return_value = acc1
    mock_acc_inst.switch_account.return_value = (True, "Switched to user2")

    # 1. account_list
    resp = clean_server.handle_request({
        "jsonrpc": "2.0", "id": 20, "method": "tools/call",
        "params": {"name": "account_list", "arguments": {}},
    })
    text = resp["result"]["content"][0]["text"]
    assert "user1@example.com" in text
    assert "[*] ACTIVE" in text
    assert "user2@example.com" in text

    # 2. account_switch
    resp = clean_server.handle_request({
        "jsonrpc": "2.0", "id": 21, "method": "tools/call",
        "params": {"name": "account_switch", "arguments": {"identifier": "2"}},
    })
    assert "Successfully switched" in resp["result"]["content"][0]["text"]

    # 3. quota_status
    mock_agg_inst = MagicMock()
    mock_agg_cls.return_value = mock_agg_inst
    mock_quota = AccountQuota(
        email="user1@example.com",
        tier_name="Standard",
        buckets=[
            QuotaBucket(model_id="gemini-3.1-pro", display_name="Gemini 3.1 Pro", percentage=80, reset_countdown="in 4h"),
            QuotaBucket(model_id="claude-3.7-sonnet", display_name="Claude 3.7 Sonnet", percentage=10, reset_countdown="in 1h"),
        ],
    )
    mock_agg_inst.fetch_single_account.return_value = mock_quota

    resp = clean_server.handle_request({
        "jsonrpc": "2.0", "id": 22, "method": "tools/call",
        "params": {"name": "quota_status", "arguments": {}},
    })
    q_text = resp["result"]["content"][0]["text"]
    assert "Gemini 3.1 Pro" in q_text
    assert "80%" in q_text
    assert "Claude 3.7 Sonnet" in q_text
    assert "Low Quota Advisory" in q_text
