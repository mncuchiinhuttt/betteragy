"""Unit tests for Betteragy persistent memory and rules MCP tools."""

from betteragy.mcp.task_db import TaskDB
from betteragy.mcp.memory_tools import (
    handle_memory_remember,
    handle_memory_recall,
    handle_memory_forget,
)


def test_memory_lifecycle(tmp_path):
    """Verify memory_remember, memory_recall, and memory_forget workflow."""
    db_file = tmp_path / "test_mem.db"
    db = TaskDB(db_file)

    # 1. Store deploy rule
    res1 = handle_memory_remember(
        {
            "key": "deploy_policy",
            "content": "Always run build and deploy after task completion",
            "category": "workflow",
        },
        db,
    )
    assert "[ok]" in res1["content"][0]["text"]
    assert "deploy_policy" in res1["content"][0]["text"]

    # 2. Store testing rule
    res2 = handle_memory_remember(
        {
            "key": "test_rule",
            "content": "Never skip failing tests just to pass CI",
            "category": "rule",
        },
        db,
    )
    assert "[ok]" in res2["content"][0]["text"]

    # 3. Recall all rules
    res_list = handle_memory_recall({}, db)
    text = res_list["content"][0]["text"]
    assert "deploy_policy" in text
    assert "test_rule" in text
    assert "Always run build" in text

    # 4. Recall with query filter
    res_filter = handle_memory_recall({"query": "deploy"}, db)
    text_filter = res_filter["content"][0]["text"]
    assert "deploy_policy" in text_filter
    assert "test_rule" not in text_filter

    # 5. Forget rule
    res_del = handle_memory_forget({"key": "test_rule"}, db)
    assert "[ok]" in res_del["content"][0]["text"]

    # Verify forgotten
    res_post_del = handle_memory_recall({"query": "test_rule"}, db)
    assert "No persistent memories" in res_post_del["content"][0]["text"]
