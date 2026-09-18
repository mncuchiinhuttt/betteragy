"""Memory and Persistent Rules tools for Betteragy MCP engine."""

import sqlite3
import time
from typing import Any, Dict, List, Optional
from pathlib import Path
from betteragy.mcp.task_db import TaskDB

MEMORY_TOOL_DEFINITIONS = [
    {
        "name": "memory_remember",
        "description": "Store a persistent rule, user preference, workflow requirement, or lesson learned (e.g. 'always deploy after tests pass', 'never push without build').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Short key or identifier (e.g. 'deploy_policy', 'test_framework')."},
                "content": {"type": "string", "description": "The exact rule, constraint, or memory to store."},
                "category": {
                    "type": "string",
                    "enum": ["rule", "preference", "workflow", "general"],
                    "description": "Category of the memory.",
                },
            },
            "required": ["key", "content"],
        },
    },
    {
        "name": "memory_recall",
        "description": "Recall and list persistent rules, instructions, or memories to avoid repeating past mistakes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Optional search term to filter memories."},
                "category": {
                    "type": "string",
                    "enum": ["rule", "preference", "workflow", "general"],
                    "description": "Optional category filter.",
                },
            },
        },
    },
    {
        "name": "memory_forget",
        "description": "Delete a stored rule or memory by its key or ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key of the rule to remove."},
            },
            "required": ["key"],
        },
    },
]


def handle_memory_remember(args: Dict[str, Any], db: TaskDB) -> Dict[str, Any]:
    key = args.get("key", "").strip()
    content = args.get("content", "").strip()
    category = args.get("category", "rule").strip()
    if not key or not content:
        return {"content": [{"type": "text", "text": "[!] 'key' and 'content' are required"}], "isError": True}

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with db._get_connection() as conn:
        conn.execute(
            """
            INSERT INTO memories (key, content, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                content = excluded.content,
                category = excluded.category,
                updated_at = excluded.updated_at
            """,
            (key, content, category, now, now),
        )

    res = f"[ok] Stored persistent memory '{key}' ({category}):\n  \"{content}\""
    return {"content": [{"type": "text", "text": res}]}


def handle_memory_recall(args: Dict[str, Any], db: TaskDB) -> Dict[str, Any]:
    query = args.get("query", "").strip().lower()
    category = args.get("category", "").strip().lower()

    sql = "SELECT id, key, content, category, updated_at FROM memories"
    params = []
    clauses = []
    if category:
        clauses.append("category = ?")
        params.append(category)
    if query:
        clauses.append("(LOWER(key) LIKE ? OR LOWER(content) LIKE ?)")
        params.extend([f"%{query}%", f"%{query}%"])

    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY updated_at DESC"

    with db._get_connection() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()

    if not rows:
        return {"content": [{"type": "text", "text": "No persistent memories or rules found matching criteria."}]}

    lines = ["=== Persistent Memory & Active Rules ==="]
    for r in rows:
        lines.append(f"  • [{r['category'].upper()}] {r['key']}: {r['content']}")
    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


def handle_memory_forget(args: Dict[str, Any], db: TaskDB) -> Dict[str, Any]:
    key = args.get("key", "").strip()
    with db._get_connection() as conn:
        cur = conn.execute("DELETE FROM memories WHERE key = ?", (key,))
        deleted = cur.rowcount

    if deleted > 0:
        return {"content": [{"type": "text", "text": f"[ok] Forgot persistent rule: '{key}'"}]}
    return {"content": [{"type": "text", "text": f"No memory found with key '{key}'"}], "isError": True}
