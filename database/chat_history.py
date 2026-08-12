from __future__ import annotations

import json
import threading
from typing import Any, Dict, List, Optional

from database.connection import execute, get_connection

_SCHEMA_READY = False
_SCHEMA_LOCK = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    id BIGSERIAL PRIMARY KEY,
    session_key TEXT UNIQUE NOT NULL,
    owner_id TEXT NOT NULL DEFAULT 'legacy',
    title TEXT NOT NULL DEFAULT 'New Chat',
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS owner_id TEXT NOT NULL DEFAULT 'legacy';
CREATE INDEX IF NOT EXISTS idx_chat_sessions_owner_updated
ON chat_sessions(owner_id, updated_at DESC, id DESC);
"""


def ensure_chat_schema() -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    with _SCHEMA_LOCK:
        if _SCHEMA_READY:
            return
        with get_connection() as connection:
            with connection.cursor() as cursor:
                for statement in SCHEMA.split(';'):
                    statement = statement.strip()
                    if statement:
                        cursor.execute(statement)
        _SCHEMA_READY = True


def save_chat(session_key: str, title: str, messages: List[Dict[str, Any]], owner_id: str = 'legacy') -> None:
    ensure_chat_schema()
    payload = json.dumps(messages, ensure_ascii=False, default=str)
    owner = str(owner_id or 'legacy')[:200]
    execute(
        """
        INSERT INTO chat_sessions(session_key, owner_id, title, messages)
        VALUES (%s, %s, %s, %s::jsonb)
        ON CONFLICT (session_key) DO UPDATE SET
            owner_id = EXCLUDED.owner_id,
            title = EXCLUDED.title,
            messages = EXCLUDED.messages,
            updated_at = NOW();
        """,
        (session_key, owner, title[:120] or "New Chat", payload),
    )


def list_recent_chats(limit: int = 15, owner_id: str = 'legacy') -> List[Dict[str, Any]]:
    ensure_chat_schema()
    safe_limit = max(1, min(int(limit), 50))
    rows = execute(
        f"""
        SELECT session_key, title, messages, created_at, updated_at
        FROM chat_sessions
        WHERE owner_id = %s
        ORDER BY updated_at DESC, id DESC
        LIMIT {safe_limit};
        """,
        (str(owner_id or 'legacy')[:200],),
        fetch="all",
    )
    return [
        {
            "session_key": row[0],
            "title": row[1],
            "messages": row[2] if isinstance(row[2], list) else json.loads(row[2] or "[]"),
            "created_at": row[3],
            "updated_at": row[4],
        }
        for row in rows
    ]


def load_chat(session_key: str, owner_id: str = 'legacy') -> Optional[Dict[str, Any]]:
    ensure_chat_schema()
    row = execute(
        """
        SELECT session_key, title, messages, created_at, updated_at
        FROM chat_sessions
        WHERE session_key = %s AND owner_id = %s;
        """,
        (session_key, str(owner_id or 'legacy')[:200]),
        fetch="one",
    )
    if not row:
        return None
    return {
        "session_key": row[0],
        "title": row[1],
        "messages": row[2] if isinstance(row[2], list) else json.loads(row[2] or "[]"),
        "created_at": row[3],
        "updated_at": row[4],
    }


def delete_chat(session_key: str, owner_id: str = 'legacy') -> None:
    ensure_chat_schema()
    execute("DELETE FROM chat_sessions WHERE session_key = %s AND owner_id = %s;", (session_key, str(owner_id or 'legacy')[:200]))
