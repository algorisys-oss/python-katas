"""SQLite3 database for kata state management."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "katas.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS katas (
            id TEXT PRIMARY KEY,
            number INTEGER NOT NULL,
            title TEXT NOT NULL,
            module TEXT NOT NULL,
            original_code TEXT NOT NULL,
            skeleton_code TEXT,
            user_code TEXT,
            tutorial_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS run_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kata_id TEXT NOT NULL REFERENCES katas(id),
            code TEXT NOT NULL,
            stdout TEXT,
            stderr TEXT,
            exit_code INTEGER,
            duration_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_run_history_kata
            ON run_history(kata_id, created_at DESC);
    """)
    # Graceful migration: add skeleton_code column if it doesn't exist yet
    try:
        conn.execute("ALTER TABLE katas ADD COLUMN skeleton_code TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass
    conn.commit()
    conn.close()


def get_kata(kata_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM katas WHERE id = ?", (kata_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_katas() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM katas ORDER BY number"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_user_code(kata_id: str, code: str):
    conn = get_db()
    conn.execute(
        "UPDATE katas SET user_code = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (code, kata_id),
    )
    conn.commit()
    conn.close()


def reset_user_code(kata_id: str) -> str:
    conn = get_db()
    row = conn.execute(
        "SELECT original_code FROM katas WHERE id = ?", (kata_id,)
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE katas SET user_code = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (kata_id,),
        )
        conn.commit()
    conn.close()
    return row["original_code"] if row else ""


def save_run(kata_id: str, code: str, stdout: str, stderr: str, exit_code: int, duration_ms: int):
    conn = get_db()
    conn.execute(
        "INSERT INTO run_history (kata_id, code, stdout, stderr, exit_code, duration_ms) VALUES (?, ?, ?, ?, ?, ?)",
        (kata_id, code, stdout, stderr, exit_code, duration_ms),
    )
    conn.commit()
    conn.close()


def upsert_kata(kata_id: str, number: int, title: str, module: str, original_code: str, tutorial_path: str, skeleton_code: str | None = None):
    conn = get_db()
    conn.execute(
        """INSERT INTO katas (id, number, title, module, original_code, skeleton_code, tutorial_path)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
             title = excluded.title,
             module = excluded.module,
             original_code = excluded.original_code,
             skeleton_code = excluded.skeleton_code,
             tutorial_path = excluded.tutorial_path,
             updated_at = CURRENT_TIMESTAMP""",
        (kata_id, number, title, module, original_code, skeleton_code, tutorial_path),
    )
    conn.commit()
    conn.close()


def get_skeleton(kata_id: str) -> str:
    """Return skeleton_code for a kata, falling back to original_code."""
    conn = get_db()
    row = conn.execute(
        "SELECT skeleton_code, original_code FROM katas WHERE id = ?", (kata_id,)
    ).fetchone()
    conn.close()
    if not row:
        return ""
    return row["skeleton_code"] or row["original_code"]


def get_solution(kata_id: str) -> str:
    """Return the full solution (original_code) for a kata."""
    conn = get_db()
    row = conn.execute(
        "SELECT original_code FROM katas WHERE id = ?", (kata_id,)
    ).fetchone()
    conn.close()
    return row["original_code"] if row else ""
