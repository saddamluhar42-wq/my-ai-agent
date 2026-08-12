from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from database.connection import execute, get_connection

TASK_SCHEMA = """
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    chat_id TEXT NOT NULL,
    task_text TEXT NOT NULL,
    due_at TIMESTAMPTZ NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    claimed_at TIMESTAMPTZ,
    executed_at TIMESTAMPTZ,
    result TEXT,
    last_error TEXT
);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_due ON scheduled_tasks(status, due_at);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_chat ON scheduled_tasks(chat_id, created_at DESC);
"""

_SCHEMA_READY = False
_SCHEMA_LOCK = threading.Lock()


def ensure_task_schema() -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    with _SCHEMA_LOCK:
        if _SCHEMA_READY:
            return
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(TASK_SCHEMA)
        _SCHEMA_READY = True


def create_task(user_id: Optional[int], chat_id: str, task_text: str, due_at: datetime, timezone: str = "Asia/Kolkata") -> int:
    ensure_task_schema()
    row = execute(
        """
        INSERT INTO scheduled_tasks (user_id, chat_id, task_text, due_at, timezone, status)
        VALUES (%s, %s, %s, %s, %s, 'pending')
        RETURNING id;
        """,
        (user_id, str(chat_id), str(task_text).strip(), due_at, timezone),
        fetch="one",
    )
    return int(row[0])


def claim_due_tasks(limit: int = 20) -> List[Dict[str, Any]]:
    ensure_task_schema()
    safe_limit = max(1, min(int(limit), 100))
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT id, user_id, chat_id, task_text, due_at, timezone, attempts
                FROM scheduled_tasks
                WHERE status = 'pending' AND due_at <= NOW()
                ORDER BY due_at ASC, id ASC
                FOR UPDATE SKIP LOCKED
                LIMIT {safe_limit};
                """
            )
            rows = cursor.fetchall()
            if not rows:
                return []
            task_ids = [row[0] for row in rows]
            cursor.execute(
                """
                UPDATE scheduled_tasks
                SET status = 'running', attempts = attempts + 1, claimed_at = NOW()
                WHERE id = ANY(%s);
                """,
                (task_ids,),
            )
    return [
        {"id": row[0], "user_id": row[1], "chat_id": row[2], "task_text": row[3], "due_at": row[4], "timezone": row[5], "attempts": int(row[6]) + 1}
        for row in rows
    ]


def complete_task(task_id: int, result: str) -> None:
    ensure_task_schema()
    execute(
        """
        UPDATE scheduled_tasks
        SET status = 'completed', executed_at = NOW(), result = %s, last_error = NULL
        WHERE id = %s;
        """,
        (str(result)[:4000], task_id),
    )


def retry_task(task_id: int, error: str, max_attempts: int = 3) -> None:
    ensure_task_schema()
    execute(
        """
        UPDATE scheduled_tasks
        SET status = CASE WHEN attempts < %s THEN 'pending' ELSE 'failed' END,
            due_at = CASE WHEN attempts < %s THEN NOW() + INTERVAL '30 seconds' ELSE due_at END,
            last_error = %s
        WHERE id = %s;
        """,
        (max_attempts, max_attempts, str(error)[:4000], task_id),
    )


def list_tasks(chat_id: str = "", limit: int = 20) -> List[Dict[str, Any]]:
    ensure_task_schema()
    safe_limit = max(1, min(int(limit), 50))
    if str(chat_id).strip():
        rows = execute(
            f"""
            SELECT id, task_text, due_at, timezone, status, attempts, created_at, executed_at, result, last_error
            FROM scheduled_tasks
            WHERE chat_id = %s
            ORDER BY due_at ASC, id DESC
            LIMIT {safe_limit};
            """,
            (str(chat_id),),
            fetch="all",
        )
    else:
        rows = execute(
            f"""
            SELECT id, task_text, due_at, timezone, status, attempts, created_at, executed_at, result, last_error
            FROM scheduled_tasks
            ORDER BY CASE WHEN status IN ('pending', 'running') THEN 0 ELSE 1 END, due_at ASC, id DESC
            LIMIT {safe_limit};
            """,
            fetch="all",
        )
    return [
        {"id": row[0], "task_text": row[1], "due_at": row[2], "timezone": row[3], "status": row[4], "attempts": row[5], "created_at": row[6], "executed_at": row[7], "result": row[8], "last_error": row[9]}
        for row in rows
    ]


def cancel_task(task_id: int, chat_id: str) -> bool:
    ensure_task_schema()
    row = execute(
        """
        UPDATE scheduled_tasks SET status = 'cancelled'
        WHERE id = %s AND chat_id = %s AND status IN ('pending', 'running')
        RETURNING id;
        """,
        (task_id, str(chat_id)),
        fetch="one",
    )
    return bool(row)
