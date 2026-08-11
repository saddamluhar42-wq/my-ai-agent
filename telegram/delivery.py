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


def deliver_previous_answer(recent_messages, chat_id: str = DEFAULT_CHAT_ID):
    if not TELEGRAM_BOT_TOKEN:
        return False, "Telegram bot token is not configured."

    answer = ""
    for message in reversed(list(recent_messages or [])):
        if not isinstance(message, dict):
            continue
        role = str(message.get("role", "")).lower().strip()
        content = str(message.get("content", "") or "").strip()
        if role == "assistant" and content:
            answer = content
            break

    if not answer:
        return False, "Previous assistant answer was not found."

    try:
        send_message(chat_id, answer)
        return True, "Telegram par previous answer successfully bhej diya."
    except TelegramError as error:
        return False, f"Telegram send failed: {error}"
    except Exception as error:
        return False, f"Telegram send failed: {error}"
