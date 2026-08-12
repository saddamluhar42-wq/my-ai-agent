from __future__ import annotations

import re
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from config import DATABASE_URL, TELEGRAM_BOT_TOKEN
from database.tasks import (
    cancel_task,
    claim_due_tasks,
    complete_task,
    create_task,
    ensure_task_schema,
    list_tasks,
    retry_task,
)
from telegram.bot import send_message

DEFAULT_TIMEZONE = "Asia/Kolkata"
POLL_INTERVAL_SECONDS = 0.5
MAX_TASK_ATTEMPTS = 3

_TIME_PATTERN = re.compile(
    r"(?<!\d)(\d{1,2})(?::(\d{2}))?\s*(am|pm)(?!\w)",
    re.IGNORECASE,
)

_TASK_HINTS = (
    "task",
    "remind",
    "reminder",
    "remember",
    "yaad",
    "yaad dil",
    "karna",
    "karo",
    "kar do",
    "jana",
    "jaana",
    "jao",
    "bhejna",
    "bhej",
    "call",
    "meeting",
    "school",
    "pickup",
    "pick up",
    "send",
    "do this",
    "go to",
    "mujhe",
)

_DATE_TOMORROW = ("tomorrow", "kal", "next day")
_DATE_TODAY = ("today", "aaj")


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _get_message_text(message: dict) -> str:
    return _clean_text(
        message.get("text") or message.get("caption")
    )


def _get_chat_id(message: dict) -> Optional[str]:
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    return str(chat_id) if chat_id is not None else None


def _get_user_id(message: dict) -> Optional[int]:
    user = message.get("from") or {}
    telegram_id = user.get("id")
    if telegram_id is None:
        return None

    try:
        from database.models import get_or_create_user

        display_name = (
            f"{user.get('first_name', '')} {user.get('last_name', '')}"
        ).strip() or user.get("username") or "Telegram User"

        return get_or_create_user(
            external_id=f"telegram:{telegram_id}",
            display_name=display_name,
        )
    except Exception:
        return None


def _is_time_question(text: str) -> bool:
    normalized = text.lower().strip()
    question_phrases = (
        "what time",
        "tell me the time",
        "time kya",
        "time bata",
        "kitne baje hai",
        "kitna time hai",
        "abhi time",
        "current time",
        "local time",
        "samay kya",
        "samay bata",
        "waqt kya",
        "waqt bata",
    )
    return any(phrase in normalized for phrase in question_phrases)


def _looks_like_task(text: str) -> bool:
    normalized = text.lower().strip()
    if not normalized or _is_time_question(normalized):
        return False
    if "?" in normalized and not any(
        marker in normalized for marker in ("remind", "yaad", "task")
    ):
        return False
    return any(hint in normalized for hint in _TASK_HINTS)


def _extract_due_at(text: str, timezone_name: str = DEFAULT_TIMEZONE) -> Optional[datetime]:
    match = _TIME_PATTERN.search(text)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = match.group(3).lower()

    if hour < 1 or hour > 12 or minute > 59:
        return None

    if meridiem == "am":
        hour = 0 if hour == 12 else hour
    else:
        hour = 12 if hour == 12 else hour + 12

    tz = ZoneInfo(timezone_name)
    now = datetime.now(tz)
    target_date = now.date()
    normalized = text.lower()

    if any(marker in normalized for marker in _DATE_TOMORROW):
        target_date += timedelta(days=1)
    elif any(marker in normalized for marker in _DATE_TODAY):
        target_date = target_date
    else:
        candidate_today = datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            hour,
            minute,
            tzinfo=tz,
        )
        if candidate_today <= now:
            target_date += timedelta(days=1)

    return datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        hour,
        minute,
        tzinfo=tz,
    )


def parse_scheduled_task(
    text: str,
    timezone_name: str = DEFAULT_TIMEZONE,
) -> Optional[Tuple[str, datetime]]:
    clean = _clean_text(text)
    if not clean or not _looks_like_task(clean):
        return None

    due_at = _extract_due_at(clean, timezone_name=timezone_name)
    if due_at is None:
        return None

    return clean, due_at


def _format_local_time(due_at: datetime, timezone_name: str) -> str:
    local = due_at.astimezone(ZoneInfo(timezone_name))
    return local.strftime("%d %b %Y, %I:%M %p").lstrip("0")


def _handle_task_command(message: dict, text: str) -> bool:
    chat_id = _get_chat_id(message)
    if not chat_id:
        return False

    normalized = text.lower().strip()
    if normalized == "/tasks" or normalized.startswith("/tasks "):
        try:
            rows = list_tasks(chat_id, limit=20)
        except Exception as exc:
            send_message(chat_id, f"Task list nahi mil saki: {str(exc)[:700]}")
            return True

        if not rows:
            send_message(chat_id, "Koi saved task nahi hai.")
            return True

        lines = ["📋 Saved Tasks"]
        for row in rows:
            due = _format_local_time(row["due_at"], row["timezone"])
            lines.append(
                f"#{row['id']} • {row['status']} • {due}\n{row['task_text']}"
            )
        send_message(chat_id, "\n\n".join(lines))
        return True

    if normalized.startswith("/cancel_task"):
        parts = normalized.split()
        if len(parts) != 2 or not parts[1].isdigit():
            send_message(chat_id, "Use: /cancel_task TASK_ID")
            return True

        task_id = int(parts[1])
        try:
            cancelled = cancel_task(task_id, chat_id)
        except Exception as exc:
            send_message(chat_id, f"Task cancel nahi hua: {str(exc)[:700]}")
            return True

        send_message(
            chat_id,
            f"{'✅ Task cancelled.' if cancelled else 'Task nahi mila ya already execute ho chuka hai.'} #{task_id}",
        )
        return True

    return False


def try_schedule_message(message: dict) -> bool:
    """Save a natural-language Telegram task when it contains an explicit time."""
    text = _get_message_text(message)
    if not text:
        return False

    if _handle_task_command(message, text):
        return True

    parsed = parse_scheduled_task(text)
    if parsed is None:
        return False

    chat_id = _get_chat_id(message)
    if not chat_id:
        return False

    if not DATABASE_URL:
        send_message(
            chat_id,
            "Task save nahi ho saka: DATABASE_URL configured nahi hai.",
        )
        return True

    try:
        ensure_task_schema()
        task_text, due_at = parsed
        task_id = create_task(
            user_id=_get_user_id(message),
            chat_id=chat_id,
            task_text=task_text,
            due_at=due_at,
            timezone=DEFAULT_TIMEZONE,
        )
        due_text = _format_local_time(due_at, DEFAULT_TIMEZONE)
        send_message(
            chat_id,
            (
                f"✅ Task saved successfully.\n\n"
                f"Task ID: #{task_id}\n"
                f"Time: {due_text} IST\n"
                f"Action: {task_text}\n\n"
                "Usi time Telegram par reminder bhejunga aur turant execution report bhi dunga."
            ),
        )
        return True
    except Exception as exc:
        send_message(
            chat_id,
            f"Task save karte waqt error aaya: {str(exc)[:900]}",
        )
        return True


def _execute_task(task: dict) -> None:
    task_id = task["id"]
    chat_id = task["chat_id"]
    task_text = task["task_text"]
    timezone_name = task["timezone"] or DEFAULT_TIMEZONE

    try:
        due_text = _format_local_time(task["due_at"], timezone_name)
        send_message(
            chat_id,
            (
                "⏰ Scheduled Task Reminder\n\n"
                f"Task #{task_id}\n"
                f"{task_text}\n\n"
                f"Scheduled time: {due_text}"
            ),
        )

        report_time = datetime.now(ZoneInfo(timezone_name)).strftime("%I:%M:%S %p").lstrip("0")
        report = (
            f"Task #{task_id} executed successfully.\n"
            f"Report time: {report_time} {timezone_name}\n"
            "Status: Delivered on schedule."
        )
        send_message(chat_id, f"✅ Execution Report\n\n{report}")
        complete_task(task_id, report)
    except Exception as exc:
        error_text = str(exc)[:1200]
        retry_task(task_id, error_text, max_attempts=MAX_TASK_ATTEMPTS)


def _scheduler_loop(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        try:
            if DATABASE_URL and TELEGRAM_BOT_TOKEN:
                ensure_task_schema()
                tasks = claim_due_tasks(limit=20)
                for task in tasks:
                    _execute_task(task)
        except Exception:
            pass

        stop_event.wait(POLL_INTERVAL_SECONDS)


class TaskScheduler:
    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> None:
        if self.running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=_scheduler_loop,
            args=(self._stop_event,),
            name="scheduled-task-worker",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=2)
        self._thread = None


scheduler = TaskScheduler()
