from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from agent.executor import ExecutionResult
from agent.task_scheduler import (
    DEFAULT_TIMEZONE,
    parse_scheduled_task,
)
from config import DATABASE_URL, TELEGRAM_BOT_TOKEN
from database.tasks import create_task, ensure_task_schema


TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def try_create_web_task(
    query: str,
    user_id=None,
) -> ExecutionResult | None:
    """Convert a timed web-chat request into a persistent Telegram task."""
    parsed = parse_scheduled_task(query, timezone_name=DEFAULT_TIMEZONE)
    if parsed is None:
        return None

    if not DATABASE_URL:
        return ExecutionResult(
            answer=(
                "Task schedule nahi hua. DATABASE_URL configured nahi hai, "
                "isliye task persist nahi kiya ja sakta."
            ),
            success=False,
            skill="scheduled_task",
            metadata={"reason": "database_not_configured"},
        )

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return ExecutionResult(
            answer=(
                "Task schedule nahi hua. Telegram Bot Token aur "
                "TELEGRAM_CHAT_ID dono configured hone chahiye."
            ),
            success=False,
            skill="scheduled_task",
            metadata={"reason": "telegram_destination_not_configured"},
        )

    task_text, due_at = parsed
    ensure_task_schema()
    task_id = create_task(
        user_id=user_id,
        chat_id=TELEGRAM_CHAT_ID,
        task_text=task_text,
        due_at=due_at,
        timezone=DEFAULT_TIMEZONE,
    )

    local_due = due_at.astimezone(ZoneInfo(DEFAULT_TIMEZONE))
    due_text = local_due.strftime("%d %b %Y, %I:%M %p").lstrip("0")

    return ExecutionResult(
        answer=(
            "✅ Task saved successfully.\n\n"
            f"Task ID: #{task_id}\n"
            f"Time: {due_text} IST\n"
            f"Task: {task_text}\n\n"
            "Usi time Telegram par reminder bheja jayega aur turant execution report bhi bheji jayegi."
        ),
        success=True,
        skill="scheduled_task",
        metadata={
            "task_id": task_id,
            "due_at": due_at.isoformat(),
            "timezone": DEFAULT_TIMEZONE,
            "telegram_chat_id_configured": True,
        },
    )
