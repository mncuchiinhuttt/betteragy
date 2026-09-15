"""Tool declarations and execution handlers for Betteragy MCP To-Do server."""

import re
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
                "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                "session_id": {"type": "integer"},
                "color": {"type": "boolean", "description": "Enable colored ANSI output."},
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
                "task_id": {"type": "integer"},
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "blocked"]},
                "evidence": {"type": "string"},
                "description": {"type": "string"},
                "color": {"type": "boolean", "description": "Enable colored ANSI output."},
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


def format_tasks_ascii_tree(
    goal: str,
    tasks: List[Dict[str, Any]],
    project_name: str = "",
    use_color: bool = False,
) -> str:
    """Format tasks as a clean single-width ASCII tree checklist with optional ANSI colors."""
    total, done = len(tasks), sum(1 for t in tasks if t["status"] == "completed")
    proj_str = f" ({project_name})" if project_name else ""
    header_goal = goal if goal else "Active Tasks"

    G, Y, R, D = ("\033[1;32m", "\033[1;33m", "\033[1;31m", "\033[0;90m") if use_color else ("", "", "", "")
    C, W, RST = ("\033[1;36m", "\033[1;37m", "\033[0m") if use_color else ("", "", "")

    lines = [f"{C}TODO{RST}", f"  {D}|--{RST} {W}{header_goal}{proj_str}{RST} · {C}{done}/{total}{RST}"]
    if not tasks:
        lines.append(f"  {D}|  '--{RST} {D}[ ] No tasks scheduled{RST}")
    else:
        for i, t in enumerate(tasks):
            is_last = (i == total - 1)
            branch = f"  {D}|  '--{RST}" if is_last else f"  {D}|  |--{RST}"
            st = t.get("status", "pending")
            m, s = (f"{G}[x]{RST}", G) if st == "completed" else (f"{Y}[>]{RST}", Y) if st == "in_progress" else (f"{R}[!]{RST}", R) if st == "blocked" else (f"{D}[ ]{RST}", D)
            suffix = f" {Y}(in_progress){RST}" if st == "in_progress" else f" {R}(blocked){RST}" if st == "blocked" else ""
            lines.append(f"{branch} {m} {s}#{t['id']} {t.get('title', '')}{RST}{suffix}")
            if t.get("evidence"):
                indent = "     " if is_last else f"  {D}|  {RST}"
                lines.append(f"{indent}  {D}Evidence: {t['evidence']}{RST}")
    lines.append(f"  {D}`-----{RST}")
    return "\n".join(lines)


def _get_tree(db: TaskDB, sid: Any, use_color: bool, status_filter: Any = None) -> str:
    tasks = db.get_tasks(session_id=sid, status_filter=status_filter)
    active = db.get_active_session(session_id=sid)
    goal = active["goal"] if active else "Active Tasks"
    proj = active.get("project_name") if active else ""
    return format_tasks_ascii_tree(goal, tasks, proj, use_color=use_color)


def execute_tool(name: str, args: Dict[str, Any], db: TaskDB) -> Dict[str, Any]:
    """Dispatch and execute an MCP tool invocation."""
    sid, use_color = args.get("session_id"), bool(args.get("color", False))

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
        ok = db.update_task(task_id=task_id, status=status, evidence=evidence, description=args.get("description"))
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
