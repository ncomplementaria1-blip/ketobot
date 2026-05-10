"""SQLite persistence for conversation history."""
import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.getenv("SQLITE_PATH", "ketobot.db")


@contextmanager
def _connect(path=None):
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(path=None):
    with _connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id, id)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                ctwa_clid TEXT,
                first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                value_clp INTEGER NOT NULL,
                event_id TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def upsert_user_referral(user_id, ctwa_clid, path=None):
    """Guarda el ctwa_clid de un usuario solo la primera vez (no sobrescribe)."""
    with _connect(path) as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, ctwa_clid) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                ctwa_clid = COALESCE(users.ctwa_clid, excluded.ctwa_clid)
            """,
            (user_id, ctwa_clid),
        )


def get_user_referral(user_id, path=None):
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT ctwa_clid FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
    return row["ctwa_clid"] if row else None


def record_sale(user_id, value_clp, event_id, path=None):
    """Inserta venta. Retorna False si event_id ya existe (deduplicación)."""
    with _connect(path) as conn:
        try:
            conn.execute(
                "INSERT INTO sales (user_id, value_clp, event_id) VALUES (?, ?, ?)",
                (user_id, value_clp, event_id),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def save_message(user_id, role, content, path=None):
    with _connect(path) as conn:
        conn.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )


def get_conversation(user_id, limit=10, path=None):
    """Return last `limit` messages for user_id, oldest first."""
    with _connect(path) as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
