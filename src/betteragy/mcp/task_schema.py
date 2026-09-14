"""SQLite DDL schema and migration helpers for Betteragy TaskDB."""

import sqlite3

INIT_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal TEXT NOT NULL,
    project_name TEXT DEFAULT '',
    working_dir TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'pending',
    evidence TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_tasks_session ON tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
"""


def init_task_db_schema(conn: sqlite3.Connection) -> None:
    """Initialize tables and run migrations if columns are missing."""
    conn.executescript(INIT_SCHEMA_SQL)
    cursor = conn.execute("PRAGMA table_info(sessions)")
    cols = {row["name"] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()}
    if "working_dir" not in cols:
        conn.execute("ALTER TABLE sessions ADD COLUMN working_dir TEXT DEFAULT ''")
    if "updated_at" not in cols:
        conn.execute("ALTER TABLE sessions ADD COLUMN updated_at TEXT DEFAULT ''")
