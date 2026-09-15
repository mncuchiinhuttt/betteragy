"""Checkpoint and persistent memory tools for long-running and multi-day agent tasks."""

import json
from typing import Any, Dict, List, Optional

from betteragy.mcp.checkpoint_db import CheckpointDB

CHECKPOINT_TOOL_DEFINITIONS = [
    {
        "name": "checkpoint_save",
        "description": "Save a structured snapshot of ongoing work (completed steps, next steps, context) for multi-day tasks or before sleeping.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Concise unique name for this checkpoint (e.g. 'auth_phase1_done')."},
                "summary": {"type": "string", "description": "Summary of accomplished progress and decisions made."},
                "next_steps": {"type": "string", "description": "Specific actionable next steps to execute upon resume."},
                "context_data": {"description": "Arbitrary dictionary or JSON string of file paths, flags, or test logs."},
                "session_id": {"type": "integer", "description": "Optional session ID to bind this checkpoint to."},
            },
            "required": ["name", "summary"],
        },
    },
    {
        "name": "checkpoint_resume",
        "description": "Resume execution context from a previously saved checkpoint (by name, ID, or latest in session).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the checkpoint to resume."},
                "checkpoint_id": {"type": "integer", "description": "ID of the checkpoint to resume."},
                "session_id": {"type": "integer", "description": "Optional session ID to look within."},
            },
        },
    },
    {
        "name": "checkpoint_list",
        "description": "List all saved execution checkpoints and their timestamps.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "integer", "description": "Optional session ID filter."},
                "limit": {"type": "integer", "description": "Max number of checkpoints to return (default 10)."},
            },
        },
    },
]


def format_checkpoint_resume_card(cp: Dict[str, Any]) -> str:
    """Render a clean ASCII resume card for the agent."""
    lines = [
        f"=== RESUMED CHECKPOINT #{cp['id']}: {cp['name']} ===",
        f"Saved At:    {cp.get('created_at', 'unknown')}",
        f"Session ID:  #{cp.get('session_id', 'none')}",
        "\n--- Progress Summary ---",
        cp.get("summary", "").strip(),
    ]
    if cp.get("next_steps"):
        lines.extend(["\n--- Immediate Next Steps ---", cp["next_steps"].strip()])
    if cp.get("context_data"):
        raw_ctx = cp["context_data"]
        try:
            parsed = json.loads(raw_ctx)
            formatted = json.dumps(parsed, indent=2)
        except Exception:
            formatted = str(raw_ctx)
        lines.extend(["\n--- Context Data ---", formatted])
    lines.append("\n[ok] Context successfully restored. Proceed with next steps.")
    return "\n".join(lines)


def handle_checkpoint_save(args: Dict[str, Any], cp_db: CheckpointDB) -> Dict[str, Any]:
    name = args.get("name", "").strip()
    summary = args.get("summary", "").strip()
    if not name or not summary:
        return {"content": [{"type": "text", "text": "Error: 'name' and 'summary' are required."}], "isError": True}

    cid = cp_db.save_checkpoint(
        name=name,
        summary=summary,
        next_steps=args.get("next_steps", ""),
        context_data=args.get("context_data", ""),
        session_id=args.get("session_id"),
    )
    msg = (
        f"[ok] Saved checkpoint #{cid} ('{name}').\n"
        f"To resume context in future turns or after sleeping: call 'checkpoint_resume(name='{name}')'."
    )
    return {"content": [{"type": "text", "text": msg}], "checkpoint_id": cid}


def handle_checkpoint_resume(args: Dict[str, Any], cp_db: CheckpointDB) -> Dict[str, Any]:
    cp = cp_db.get_checkpoint(
        checkpoint_id=args.get("checkpoint_id"),
        name=args.get("name"),
        session_id=args.get("session_id"),
    )
    if not cp:
        ident = args.get("name") or args.get("checkpoint_id") or "latest"
        return {"content": [{"type": "text", "text": f"[!] Checkpoint '{ident}' not found."}], "isError": True}
    return {"content": [{"type": "text", "text": format_checkpoint_resume_card(cp)}]}


def handle_checkpoint_list(args: Dict[str, Any], cp_db: CheckpointDB) -> Dict[str, Any]:
    limit = int(args.get("limit", 10))
    items = cp_db.list_checkpoints(session_id=args.get("session_id"), limit=limit)
    if not items:
        return {"content": [{"type": "text", "text": "No saved checkpoints found in database."}]}

    lines = ["=== Saved Execution Checkpoints ==="]
    for cp in items:
        lines.append(
            f"  [*] #{cp['id']} [{cp['created_at'][:16]}] {cp['name']} (session #{cp.get('session_id', '?')})\n"
            f"      Summary: {cp['summary'][:80]}..."
        )
    return {"content": [{"type": "text", "text": "\n".join(lines)}]}
