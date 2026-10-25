"""Bounded, server-side conversation memory backed by SQLite.

Set JARVIS_DB_PATH to a durable path in environments with persistent storage.
Render Free web services have ephemeral filesystems, so their local SQLite file
is lost when an instance spins down or restarts.
"""
import os
import sqlite3
import time
from typing import Dict, List

DEFAULT_DB_PATH = os.path.join(os.getenv("TMPDIR", "/tmp"), "jarvis_memory.sqlite3")
DEFAULT_RETENTION_DAYS = 30
MAX_MESSAGES_PER_CONVERSATION = 80
MAX_HISTORY_MESSAGES = 12


def _db_path() -> str:
    return os.path.abspath(os.getenv("JARVIS_DB_PATH", DEFAULT_DB_PATH).strip() or DEFAULT_DB_PATH)


def _retention_days() -> int:
    try:
        return max(1, min(365, int(os.getenv("JARVIS_MEMORY_RETENTION_DAYS", str(DEFAULT_RETENTION_DAYS)))))
    except (TypeError, ValueError):
        return DEFAULT_RETENTION_DAYS


def _connect() -> sqlite3.Connection:
    path = _db_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_conversation_messages_id "
        "ON conversation_messages(conversation_id, id)"
    )
    return connection


def get_recent_history(conversation_id: str, limit: int = MAX_HISTORY_MESSAGES) -> List[Dict[str, str]]:
    """Return recent messages in chronological order; never return more than 12 messages."""
    safe_limit = max(0, min(MAX_HISTORY_MESSAGES, int(limit)))
    if not conversation_id or safe_limit == 0:
        return []
    now = int(time.time())
    cutoff = now - _retention_days() * 86400
    connection = _connect()
    try:
        connection.execute("DELETE FROM conversation_messages WHERE created_at < ?", (cutoff,))
        rows = connection.execute(
            """
            SELECT role, content FROM conversation_messages
            WHERE conversation_id = ? AND created_at >= ?
            ORDER BY id DESC LIMIT ?
            """,
            (conversation_id, cutoff, safe_limit),
        ).fetchall()
        connection.commit()
        return [{"role": str(role), "content": str(content)} for role, content in reversed(rows)]
    finally:
        connection.close()


def save_turn(conversation_id: str, user_message: str, assistant_reply: str) -> None:
    """Atomically store one successful user/assistant turn with retention bounds."""
    if not conversation_id:
        return
    now = int(time.time())
    cutoff = now - _retention_days() * 86400
    connection = _connect()
    try:
        with connection:
            connection.execute(
                "INSERT INTO conversation_messages(conversation_id, role, content, created_at) VALUES (?, 'user', ?, ?)",
                (conversation_id, str(user_message)[:4000], now),
            )
            connection.execute(
                "INSERT INTO conversation_messages(conversation_id, role, content, created_at) VALUES (?, 'assistant', ?, ?)",
                (conversation_id, str(assistant_reply)[:8000], now),
            )
            connection.execute("DELETE FROM conversation_messages WHERE created_at < ?", (cutoff,))
            connection.execute(
                """
                DELETE FROM conversation_messages
                WHERE conversation_id = ? AND id NOT IN (
                    SELECT id FROM conversation_messages
                    WHERE conversation_id = ? ORDER BY id DESC LIMIT ?
                )
                """,
                (conversation_id, conversation_id, MAX_MESSAGES_PER_CONVERSATION),
            )
    finally:
        connection.close()
