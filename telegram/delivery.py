import re

from config import TELEGRAM_BOT_TOKEN
from telegram.bot import TelegramError, send_message

DEFAULT_CHAT_ID = "6910692570"


def is_delivery_request(text: str) -> bool:
    value = str(text or "").strip().lower()
    if not value:
        return False
    patterns = (
        r"telegram.*(bot|par|send|bhej)",
        r"(bot|telegram).*(par|ko).*(send|bhej)",
        r"iska jawab.*(telegram|bot)",
        r"ye.*(telegram|bot).*(bhej|send)",
        r"previous answer.*(telegram|bot)",
    )
    return any(re.search(pattern, value) for pattern in patterns)


def _get_live_chat_messages():
    """Return the currently visible Streamlit chat history when available."""
    try:
        import streamlit as st

        messages = st.session_state.get("messages", [])
        if isinstance(messages, list) and messages:
            return messages
    except Exception:
        pass
    return []


def _find_latest_assistant_answer(messages):
    """Find the newest real assistant text answer from the supplied history."""
    for message in reversed(list(messages or [])):
        if not isinstance(message, dict):
            continue

        role = str(message.get("role", "")).strip().lower()
        content = str(message.get("content", "") or "").strip()
        message_type = str(message.get("type", "text") or "text").strip().lower()

        if role != "assistant" or not content:
            continue

        # Never send status placeholders or generated-media markers as a text answer.
        if content.startswith("[") and content.endswith("]"):
            continue

        if message_type not in {"text", ""}:
            continue

        return content

    return ""


def deliver_previous_answer(recent_messages, chat_id: str = DEFAULT_CHAT_ID):
    if not TELEGRAM_BOT_TOKEN:
        return False, "Telegram bot token is not configured."

    # The Streamlit session is the authoritative live conversation. The old
    # implementation relied only on the database history, which could select
    # a stale assistant answer. Use the visible live chat first and only fall
    # back to PostgreSQL history when the live session is unavailable.
    live_messages = _get_live_chat_messages()
    answer = _find_latest_assistant_answer(live_messages)

    if not answer:
        answer = _find_latest_assistant_answer(recent_messages)

    if not answer:
        return False, "Previous assistant answer was not found."

    try:
        send_message(chat_id, answer)
        return True, "Telegram par previous answer successfully bhej diya."
    except TelegramError as error:
        return False, f"Telegram send failed: {error}"
    except Exception as error:
        return False, f"Telegram send failed: {error}"
