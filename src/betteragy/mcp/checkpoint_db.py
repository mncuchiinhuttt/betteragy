"""SQLite persistence layer for Betteragy long-running task checkpoints."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .task_db import DEFAULT_DB_PATH, _now_iso
from .task_schema import init_task_db_schema


class CheckpointDB:
    """Manages persistent task checkpoints for multi-day and long-running execution."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is None or str(db_path) == ":memory:":
            self.db_path = str(db_path) if db_path else str(DEFAULT_DB_PATH)
        else:
            self.db_path = str(db_path)
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._mem_conn = sqlite3.connect(":memory:") if self.db_path == ":memory:" else None
        if self._mem_conn:
            self._mem_conn.row_factory = sqlite3.Row
        with self._get_connection() as conn:
            init_task_db_schema(conn)

    def _get_connection(self) -> sqlite3.Connection:
        if self._mem_conn:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def save_checkpoint(
        self,
        name: str,
        summary: str,
        next_steps: str = "",
        context_data: Any = "",
        session_id: Optional[int] = None,
    ) -> int:
        """Save a new execution checkpoint snapshot."""
        now = _now_iso()
        ctx_str = context_data if isinstance(context_data, str) else json.dumps(context_data)
        with self._get_connection() as conn:
            if session_id is None:
                row = conn.execute("SELECT id FROM sessions WHERE is_active = 1 ORDER BY id DESC LIMIT 1").fetchone()
                session_id = row["id"] if row else None

            cur = conn.execute(
                "INSERT INTO checkpoints (session_id, name, summary, next_steps, context_data, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, name.strip(), summary.strip(), next_steps.strip(), ctx_str, now),
            )
            return cur.lastrowid or 0

    def get_checkpoint(
        self,
        checkpoint_id: Optional[int] = None,
        name: Optional[str] = None,
        session_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a checkpoint by ID, name, or latest in session."""
        with self._get_connection() as conn:
            if checkpoint_id is not None:
                row = conn.execute("SELECT * FROM checkpoints WHERE id = ?", (checkpoint_id,)).fetchone()
            elif name:
                query = "SELECT * FROM checkpoints WHERE name = ?"
                params: List[Any] = [name.strip()]
                if session_id is not None:
                    query += " AND session_id = ?"
                    params.append(session_id)
                query += " ORDER BY id DESC LIMIT 1"
                row = conn.execute(query, params).fetchone()
            elif session_id is not None:
                row = conn.execute(
                    "SELECT * FROM checkpoints WHERE session_id = ? ORDER BY id DESC LIMIT 1",
                    (session_id,),
                ).fetchone()
            else:
                row = conn.execute("SELECT * FROM checkpoints ORDER BY id DESC LIMIT 1").fetchone()
            return dict(row) if row else None

    def list_checkpoints(self, session_id: Optional[int] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """List checkpoints ordered by creation time descending."""
        with self._get_connection() as conn:
            if session_id is not None:
                rows = conn.execute(
                    "SELECT * FROM checkpoints WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                    (session_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM checkpoints ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    def delete_checkpoint(self, checkpoint_id: int) -> bool:
        """Delete a checkpoint by ID."""
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM checkpoints WHERE id = ?", (checkpoint_id,))
            return cur.rowcount > 0
