from __future__ import annotations

import os
from zoneinfo import ZoneInfo

from agent.executor import ExecutionResult
from agent.task_scheduler import DEFAULT_TIMEZONE, parse_scheduled_task
from config import DATABASE_URL, TELEGRAM_BOT_TOKEN
from database.tasks import create_task, ensure_task_schema, get_default_telegram_chat_id
from telegram.delivery import DEFAULT_CHAT_ID


def _resolve_telegram_chat_id() -> str:
    """Resolve the destination for tasks created from Streamlit.

    Priority:
    1. Render TELEGRAM_CHAT_ID environment variable
    2. Last chat ID captured by the Telegram polling worker
    3. Configured default Telegram destination
    """
    configured = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if configured:
        return configured

    try:
        remembered = get_default_telegram_chat_id().strip()
        if remembered:
            return remembered
    except Exception:
        pass

    return str(DEFAULT_CHAT_ID).strip()


def try_create_web_task(query: str, user_id=None) -> ExecutionResult | None:
    """Convert a timed Streamlit request into a persistent Telegram task."""
    parsed = parse_scheduled_task(query, timezone_name=DEFAULT_TIMEZONE)
    if parsed is None:
        return None

    if not DATABASE_URL:
        message = "Task schedule nahi hua: DATABASE_URL configured nahi hai."
        return ExecutionResult(
            answer=message,
            success=False,
            skill="scheduled_task",
            metadata={"reason": "database_not_configured", "error": message},
        )

    if not TELEGRAM_BOT_TOKEN:
        message = "Task schedule nahi hua: Telegram Bot Token configured nahi hai."
        return ExecutionResult(
            answer=message,
            success=False,
            skill="scheduled_task",
            metadata={"reason": "telegram_token_not_configured", "error": message},
        )

    try:
        chat_id = _resolve_telegram_chat_id()
    except Exception as exc:
        message = f"Task schedule nahi hua: Telegram destination read nahi ho saki: {str(exc)[:500]}"
        return ExecutionResult(
            answer=message,
            success=False,
            skill="scheduled_task",
            metadata={"reason": "telegram_destination_read_failed", "error": message},
        )

    if not chat_id:
        message = "Task schedule nahi hua: Telegram destination available nahi hai. Render me TELEGRAM_CHAT_ID set karo ya bot ko ek message bhejo."
        return ExecutionResult(
            answer=message,
            success=False,
            skill="scheduled_task",
            metadata={"reason": "telegram_destination_not_known", "error": message},
        )

    try:
        task_text, due_at = parsed
        ensure_task_schema()
        task_id = create_task(
            user_id=user_id,
            chat_id=chat_id,
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
                "Usi time Telegram par reminder aur turant execution report bheji jayegi."
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
    except Exception as exc:
        message = f"Task schedule karte waqt database error aaya: {str(exc)[:900]}"
        return ExecutionResult(
            answer=message,
            success=False,
            skill="scheduled_task",
            metadata={"reason": "task_persist_failed", "error": message},
        )
