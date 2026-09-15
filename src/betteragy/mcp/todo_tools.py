"""Tool declarations and execution dispatcher for Betteragy MCP engine."""

import re
from typing import Any, Dict, List, Optional

from betteragy.mcp.checkpoint_db import CheckpointDB
from betteragy.mcp.checkpoint_tools import (
    CHECKPOINT_TOOL_DEFINITIONS,
    handle_checkpoint_list,
    handle_checkpoint_resume,
    handle_checkpoint_save,
)
from betteragy.mcp.quota_tools import (
    QUOTA_TOOL_DEFINITIONS,
    handle_account_list,
    handle_account_switch,
    handle_quota_status,
)
from betteragy.mcp.task_db import TaskDB
from betteragy.mcp.tree_formatter import check_dependencies, format_tasks_ascii_tree

TODO_TOOL_DEFINITIONS = [
    {
        "name": "todo_init",
        "description": "Initialize a new task execution session with an overarching goal and project name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "The high-level objective to accomplish."},
                "project_name": {"type": "string", "description": "Optional project or repo name."},
                "working_dir": {"type": "string", "description": "Optional working directory path."},
                "color": {"type": "boolean", "description": "Enable colored ANSI output."},
            },
            "required": ["goal"],
        },
    },
    {
        "name": "todo_add",
        "description": "Add an atomic subtask with optional subagent assignment and dependency constraints.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Concise title of the atomic subtask."},
                "description": {"type": "string", "description": "Implementation details or checklist."},
                "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                "assigned_to": {"type": "string", "description": "Subagent role or worker name (e.g. 'researcher', 'reviewer')."},
                "depends_on": {"type": "string", "description": "ID or comma-separated IDs of prerequisite tasks."},
                "session_id": {"type": "integer"},
                "color": {"type": "boolean", "description": "Enable colored ANSI output."},
            },
            "required": ["title"],
        },
    },
    {
        "name": "todo_update",
        "description": "Update task status, evidence, subagent assignment, or dependencies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer"},
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "blocked"]},
                "evidence": {"type": "string"},
                "description": {"type": "string"},
                "assigned_to": {"type": "string"},
                "depends_on": {"type": "string"},
                "color": {"type": "boolean", "description": "Enable colored ANSI output."},
            },
            "required": ["task_id", "status"],
        },
    },
    {
        "name": "todo_list",
        "description": "Get current list of tasks and overall progress with dependency badges.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "blocked"]},
                "session_id": {"type": "integer"},
                "color": {"type": "boolean", "description": "Enable colored ANSI output."},
            },
        },
    },
    {
        "name": "todo_clear",
        "description": "Clear all tasks in the session.",
        "inputSchema": {
            "type": "object",
            "properties": {"session_id": {"type": "integer"}},
        },
    },
]

ALL_TOOL_DEFINITIONS = TODO_TOOL_DEFINITIONS + QUOTA_TOOL_DEFINITIONS + CHECKPOINT_TOOL_DEFINITIONS
TOOL_DEFINITIONS = ALL_TOOL_DEFINITIONS


def _get_tree(db: TaskDB, sid: Any, use_color: bool, status_filter: Any = None) -> str:
    tasks = db.get_tasks(session_id=sid, status_filter=status_filter)
    active = db.get_active_session(session_id=sid)
    goal = active["goal"] if active else "Active Tasks"
    proj = active.get("project_name") if active else ""
    return format_tasks_ascii_tree(goal, tasks, proj, use_color=use_color)


def execute_tool(name: str, args: Dict[str, Any], db: TaskDB, cp_db: Optional[CheckpointDB] = None) -> Dict[str, Any]:
    """Dispatch and execute an MCP tool invocation across all tool suites."""
    sid, use_color = args.get("session_id"), bool(args.get("color", False))
    cp_db = cp_db or CheckpointDB(db.db_path)

    if name == "quota_status":
        return handle_quota_status(args)
    if name == "account_list":
        return handle_account_list(args)
    if name == "account_switch":
        return handle_account_switch(args)
    if name == "checkpoint_save":
        return handle_checkpoint_save(args, cp_db)
    if name == "checkpoint_resume":
        return handle_checkpoint_resume(args, cp_db)
    if name == "checkpoint_list":
        return handle_checkpoint_list(args, cp_db)

    if name == "todo_init":
        session_id = db.init_session(
            goal=args.get("goal", ""),
            project_name=args.get("project_name", ""),
            working_dir=args.get("working_dir", ""),
        )
        tree = _get_tree(db, session_id, use_color)
        text = f"Initialized task session #{session_id}: {args.get('goal')}\n\n{tree}"
        return {"content": [{"type": "text", "text": text}], "session_id": session_id}

    if name == "todo_add":
        task_id = db.add_task(
            title=args.get("title", ""),
            description=args.get("description", ""),
            priority=args.get("priority", "medium"),
            session_id=sid,
            assigned_to=args.get("assigned_to", ""),
            depends_on=args.get("depends_on", ""),
        )
        tree = _get_tree(db, sid, use_color)
        text = f"Added task #{task_id}: '{args.get('title')}'\n\n{tree}"
    elif name == "todo_update":
        raw_id = args.get("task_id", 0)
        try:
            task_id = int(raw_id)
        except (ValueError, TypeError):
            m = re.search(r"\d+", str(raw_id))
            task_id = int(m.group(0)) if m else 0

        status, evidence = args.get("status", "pending"), args.get("evidence", "")
        ok = db.update_task(
            task_id=task_id, status=status, evidence=evidence,
            description=args.get("description"),
            assigned_to=args.get("assigned_to"),
            depends_on=args.get("depends_on"),
        )
        if ok:
            tree = _get_tree(db, sid, use_color)
            text = f"Task #{task_id} updated to '{status}'\n\n{tree}"
        else:
            text = f"Task #{task_id} not found"
    elif name == "todo_list":
        text = _get_tree(db, sid, use_color, status_filter=args.get("status"))
    elif name == "todo_clear":
        count = db.clear_tasks(session_id=sid)
        text = f"Cleared {count} task(s) from database."
    else:
        return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}

    return {"content": [{"type": "text", "text": text}]}
