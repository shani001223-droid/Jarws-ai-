"""Bounded SQLite memory. Render Free storage is ephemeral across restarts."""
import os, sqlite3, time
from typing import Dict, List
from .config import get_settings
MAX_MESSAGES_PER_CONVERSATION = 80
MAX_HISTORY_MESSAGES = 12

def _connect() -> sqlite3.Connection:
    settings = get_settings()
    folder = os.path.dirname(settings.db_path)
    if folder: os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(settings.db_path, timeout=5)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS conversation_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('user','assistant')),
        content TEXT NOT NULL,
        created_at INTEGER NOT NULL
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_conversation_messages_id ON conversation_messages(conversation_id, id)")
    return conn

def get_recent_history(conversation_id: str, limit: int = MAX_HISTORY_MESSAGES) -> List[Dict[str, str]]:
    safe_limit = max(0, min(MAX_HISTORY_MESSAGES, int(limit)))
    if not conversation_id or safe_limit == 0: return []
    now = int(time.time()); cutoff = now - get_settings().memory_retention_days * 86400
    conn = _connect()
    try:
        conn.execute("DELETE FROM conversation_messages WHERE created_at < ?", (cutoff,))
        rows = conn.execute("SELECT role, content FROM conversation_messages WHERE conversation_id=? AND created_at>=? ORDER BY id DESC LIMIT ?", (conversation_id, cutoff, safe_limit)).fetchall()
        conn.commit()
        return [{"role": str(role), "content": str(content)} for role, content in reversed(rows)]
    finally: conn.close()

def save_turn(conversation_id: str, user_message: str, assistant_reply: str) -> None:
    if not conversation_id: return
    now = int(time.time()); cutoff = now - get_settings().memory_retention_days * 86400
    conn = _connect()
    try:
        with conn:
            conn.execute("INSERT INTO conversation_messages(conversation_id,role,content,created_at) VALUES(?, 'user', ?, ?)", (conversation_id, str(user_message)[:4000], now))
            conn.execute("INSERT INTO conversation_messages(conversation_id,role,content,created_at) VALUES(?, 'assistant', ?, ?)", (conversation_id, str(assistant_reply)[:8000], now))
            conn.execute("DELETE FROM conversation_messages WHERE created_at < ?", (cutoff,))
            conn.execute("""DELETE FROM conversation_messages WHERE conversation_id=? AND id NOT IN
                (SELECT id FROM conversation_messages WHERE conversation_id=? ORDER BY id DESC LIMIT ?)""", (conversation_id, conversation_id, MAX_MESSAGES_PER_CONVERSATION))
    finally: conn.close()
