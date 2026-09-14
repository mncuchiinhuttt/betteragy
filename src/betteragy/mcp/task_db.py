"""SQLite persistence layer for Betteragy To-Do task planning engine."""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = Path.home() / ".config" / "betteragy" / "tasks.db"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


from .task_schema import init_task_db_schema


class TaskDB:
    """Manages atomic SQLite task records in WAL mode."""

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

    def init_session(self, goal: str, project_name: str = "", working_dir: str = "") -> int:
        now = _now_iso()
        with self._get_connection() as conn:
            conn.execute("UPDATE sessions SET is_active = 0 WHERE is_active = 1")
            cur = conn.execute(
                "INSERT INTO sessions (goal, project_name, working_dir, created_at, updated_at, is_active) "
                "VALUES (?, ?, ?, ?, ?, 1)",
                (goal, project_name, working_dir, now, now),
            )
            return cur.lastrowid or 0

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT s.*, COUNT(t.id) as total_tasks, "
                "SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks "
                "FROM sessions s LEFT JOIN tasks t ON s.id = t.session_id "
                "WHERE s.id = ? GROUP BY s.id",
                (session_id,),
            ).fetchone()
            return dict(row) if row else None

    def get_active_session(self, session_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        if session_id is not None:
            return self.get_session(session_id)
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT s.*, COUNT(t.id) as total_tasks, "
                "SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks "
                "FROM sessions s LEFT JOIN tasks t ON s.id = t.session_id "
                "WHERE s.is_active = 1 GROUP BY s.id "
                "ORDER BY COALESCE(NULLIF(s.updated_at, ''), s.created_at) DESC, s.id DESC LIMIT 1"
            ).fetchone()
            if row:
                return dict(row)
            fallback = conn.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 1").fetchone()
            return dict(fallback) if fallback else None

    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT s.*, COUNT(t.id) as total_tasks, "
                "SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks, "
                "SUM(CASE WHEN t.status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks "
                "FROM sessions s LEFT JOIN tasks t ON s.id = t.session_id GROUP BY s.id "
                "ORDER BY COALESCE(NULLIF(s.updated_at, ''), s.created_at) DESC, s.id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def set_active_session(self, session_id: int) -> bool:
        now = _now_iso()
        with self._get_connection() as conn:
            conn.execute("UPDATE sessions SET is_active = 0")
            cur = conn.execute(
                "UPDATE sessions SET is_active = 1, updated_at = ? WHERE id = ?",
                (now, session_id),
            )
            return cur.rowcount > 0

    def delete_session(self, session_id: int) -> bool:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM tasks WHERE session_id = ?", (session_id,))
            cur = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            return cur.rowcount > 0

    def add_task(
        self, title: str, description: str = "", priority: str = "medium", session_id: Optional[int] = None
    ) -> int:
        if session_id is None:
            active = self.get_active_session()
            session_id = active["id"] if active else self.init_session("Default Session")

        now = _now_iso()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO tasks (session_id, title, description, priority, status, evidence, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, 'pending', '', ?, ?)",
                (session_id, title, description, priority.lower(), now, now),
            )
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
            return cursor.lastrowid or 0

    def update_task(
        self, task_id: int, status: str, evidence: str = "", description: Optional[str] = None
    ) -> bool:
        now = _now_iso()
        valid_statuses = {"pending", "in_progress", "completed", "blocked"}
        clean_status = status.lower().strip() if status.lower().strip() in valid_statuses else "pending"

        with self._get_connection() as conn:
            if description:
                cursor = conn.execute(
                    "UPDATE tasks SET status = ?, evidence = ?, description = ?, updated_at = ? WHERE id = ?",
                    (clean_status, evidence, description, now, task_id),
                )
            else:
                cursor = conn.execute(
                    "UPDATE tasks SET status = ?, evidence = ?, updated_at = ? WHERE id = ?",
                    (clean_status, evidence, now, task_id),
                )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = (SELECT session_id FROM tasks WHERE id = ?)",
                (now, task_id),
            )
            return cursor.rowcount > 0

    def get_tasks(
        self, session_id: Optional[int] = None, status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if session_id is None:
            active = self.get_active_session()
            if not active:
                return []
            session_id = active["id"]

        query = "SELECT * FROM tasks WHERE session_id = ?"
        params: List[Any] = [session_id]
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter.lower())
        query += " ORDER BY id ASC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def clear_tasks(self, session_id: Optional[int] = None) -> int:
        with self._get_connection() as conn:
            if session_id is not None:
                cur = conn.execute("DELETE FROM tasks WHERE session_id = ?", (session_id,))
            else:
                cur = conn.execute("DELETE FROM tasks")
                conn.execute("DELETE FROM sessions")
            return cur.rowcount
