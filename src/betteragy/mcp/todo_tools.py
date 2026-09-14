"""Tool declarations and execution handlers for Betteragy MCP To-Do server."""

import json
from typing import Any, Dict, List

from betteragy.mcp.task_db import TaskDB

TOOL_DEFINITIONS = [
    {
        "name": "todo_init",
        "description": "Initialize a new task execution session with an overarching goal and project name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "The high-level objective to accomplish."},
                "project_name": {"type": "string", "description": "Optional project or repo name."},
                "working_dir": {"type": "string", "description": "Optional working directory path."},
            },
            "required": ["goal"],
        },
    },
    {
        "name": "todo_add",
        "description": "Add an atomic subtask to the execution plan.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Concise title of the atomic subtask."},
                "description": {"type": "string", "description": "Implementation details or checklist."},
                "priority": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Task priority level.",
                },
                "session_id": {"type": "integer", "description": "Optional session ID to bind task to."},
            },
            "required": ["title"],
        },
    },
    {
        "name": "todo_update",
        "description": "Update task status and document verification evidence.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task to update."},
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "blocked"],
                    "description": "New status for the task.",
                },
                "evidence": {
                    "type": "string",
                    "description": "Concrete proof of verification (e.g. test output, compile log).",
                },
                "description": {"type": "string", "description": "Optional updated description."},
            },
            "required": ["task_id", "status"],
        },
    },
    {
        "name": "todo_list",
        "description": "Get current list of tasks and overall progress.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "blocked"],
                    "description": "Optional status filter.",
                },
                "session_id": {"type": "integer", "description": "Optional session ID to list tasks from."},
            },
        },
    },
    {
        "name": "todo_clear",
        "description": "Clear all tasks in the session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "integer", "description": "Optional session ID to clear."},
            },
        },
    },
]


def format_tasks_ascii_tree(goal: str, tasks: List[Dict[str, Any]], project_name: str = "") -> str:
    """Format tasks as a clean single-width ASCII tree checklist."""
    total = len(tasks)
    done = sum(1 for t in tasks if t["status"] == "completed")
    proj_str = f" ({project_name})" if project_name else ""
    header_goal = goal if goal else "Active Tasks"

    lines = ["TODO"]
    lines.append(f"  |-- {header_goal}{proj_str} · {done}/{total}")
    if not tasks:
        lines.append("  |  '-- [ ] No tasks scheduled")
    else:
        for i, t in enumerate(tasks):
            is_last = (i == total - 1)
            branch = "  |  '--" if is_last else "  |  |--"
            status = t.get("status", "pending")
            marker = {"completed": "[x]", "in_progress": "[>]", "pending": "[ ]", "blocked": "[!]"}.get(status, "[ ]")
            title = t.get("title", "")
            suffix = ""
            if status == "in_progress":
                suffix = " (in_progress)"
            elif status == "blocked":
                suffix = " (blocked)"
            lines.append(f"{branch} {marker} #{t['id']} {title}{suffix}")
            if t.get("evidence"):
                indent = "     " if is_last else "  |  "
                lines.append(f"{indent}  Evidence: {t['evidence']}")
    lines.append("  `-----")
    return "\n".join(lines)


def execute_tool(name: str, args: Dict[str, Any], db: TaskDB) -> Dict[str, Any]:
    """Dispatch and execute an MCP tool invocation."""
    sid = args.get("session_id")

    if name == "todo_init":
        session_id = db.init_session(
            goal=args.get("goal", ""),
            project_name=args.get("project_name", ""),
            working_dir=args.get("working_dir", ""),
        )
        text = f"Initialized task session #{session_id}: {args.get('goal')}"
        return {"content": [{"type": "text", "text": text}], "session_id": session_id}

    if name == "todo_add":
        task_id = db.add_task(
            title=args.get("title", ""),
            description=args.get("description", ""),
            priority=args.get("priority", "medium"),
            session_id=sid,
        )
        text = f"Added task #{task_id}: '{args.get('title')}' [priority: {args.get('priority', 'medium')}]"
    elif name == "todo_update":
        raw_id = args.get("task_id", 0)
        try:
            task_id = int(raw_id)
        except (ValueError, TypeError):
            import re
            m = re.search(r"\d+", str(raw_id))
            task_id = int(m.group(0)) if m else 0

        status = args.get("status", "pending")
        evidence = args.get("evidence", "")
        desc = args.get("description")
        ok = db.update_task(task_id=task_id, status=status, evidence=evidence, description=desc)
        text = f"Task #{task_id} updated to '{status}'" if ok else f"Task #{task_id} not found"
    elif name == "todo_list":
        tasks = db.get_tasks(session_id=sid, status_filter=args.get("status"))
        active = db.get_active_session(session_id=sid)
        goal = active["goal"] if active else "No active goal"
        proj = active.get("project_name") if active else ""
        text = format_tasks_ascii_tree(goal, tasks, proj)
    elif name == "todo_clear":
        count = db.clear_tasks(session_id=sid)
        text = f"Cleared {count} task(s) from database."
    else:
        return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}

    return {"content": [{"type": "text", "text": text}]}
