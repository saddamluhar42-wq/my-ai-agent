import re

from config import TELEGRAM_BOT_TOKEN
from telegram.bot import TelegramError, send_message, send_photo

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
        r"(image|photo|picture|tasveer|image ko).*(telegram|bot).*(bhej|send)",
        r"(telegram|bot).*(image|photo|picture|tasveer).*(bhej|send)",
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


def _find_latest_assistant_message(messages):
    """Find the newest assistant result, including generated media."""
    for message in reversed(list(messages or [])):
        if not isinstance(message, dict):
            continue
        if str(message.get("role", "")).strip().lower() != "assistant":
            continue

        message_type = str(message.get("type", "text") or "text").strip().lower()
        if message_type == "image" and message.get("image"):
            return {"type": "image", "image": message["image"]}

        content = str(message.get("content", "") or "").strip()
        if content and message_type in {"text", ""}:
            if not (content.startswith("[") and content.endswith("]")):
                return {"type": "text", "content": content}

    return None


def _find_latest_assistant_answer(messages):
    """Find the newest real assistant text answer from the supplied history."""
    result = _find_latest_assistant_message(messages)
    if result and result.get("type") == "text":
        return result.get("content", "")
    return ""


def _send_result(result, chat_id: str):
    if not result:
        return False, "Previous assistant result was not found."

    if result.get("type") == "image":
        try:
            send_photo(
                chat_id,
                result.get("image"),
                caption="Generated image from My AI Agent",
            )
            return True, "Image Telegram par successfully bhej di."
        except TelegramError as error:
            return False, f"Telegram image send failed: {error}"
        except Exception as error:
            return False, f"Telegram image send failed: {error}"

    try:
        send_message(chat_id, result.get("content", ""))
        return True, "Telegram par previous answer successfully bhej diya."
    except TelegramError as error:
        return False, f"Telegram send failed: {error}"
    except Exception as error:
        return False, f"Telegram send failed: {error}"


def deliver_previous_answer(recent_messages, chat_id: str = DEFAULT_CHAT_ID):
    if not TELEGRAM_BOT_TOKEN:
        return False, "Telegram bot token is not configured."

    # Streamlit's live session is authoritative. This preserves generated
    # images as bytes instead of trying to turn them into text.
    live_messages = _get_live_chat_messages()
    result = _find_latest_assistant_message(live_messages)

    if not result:
        result = _find_latest_assistant_message(recent_messages)

    return _send_result(result, chat_id)
