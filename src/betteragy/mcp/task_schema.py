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
    assigned_to TEXT DEFAULT '',
    depends_on TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(id)
);
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    name TEXT NOT NULL,
    summary TEXT NOT NULL,
    next_steps TEXT DEFAULT '',
    context_data TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_tasks_session ON tasks(session_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_checkpoints_session ON checkpoints(session_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_name ON checkpoints(name);
"""


def init_task_db_schema(conn: sqlite3.Connection) -> None:
    """Initialize tables and run migrations if columns are missing."""
    conn.executescript(INIT_SCHEMA_SQL)
    # Check sessions migrations
    cursor = conn.execute("PRAGMA table_info(sessions)")
    s_cols = {row["name"] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()}
    if "working_dir" not in s_cols:
        conn.execute("ALTER TABLE sessions ADD COLUMN working_dir TEXT DEFAULT ''")
    if "updated_at" not in s_cols:
        conn.execute("ALTER TABLE sessions ADD COLUMN updated_at TEXT DEFAULT ''")

    # Check tasks migrations
    cursor = conn.execute("PRAGMA table_info(tasks)")
    t_cols = {row["name"] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()}
    if "assigned_to" not in t_cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN assigned_to TEXT DEFAULT ''")
    if "depends_on" not in t_cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN depends_on TEXT DEFAULT ''")
