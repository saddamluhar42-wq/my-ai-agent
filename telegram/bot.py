import json
import urllib.error
import urllib.request

from config import (
    REQUEST_TIMEOUT,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_MESSAGE_LIMIT,
    TELEGRAM_URL,
)


class TelegramError(Exception):
    """Raised when Telegram Bot API fails."""


def is_configured():
    return bool(TELEGRAM_BOT_TOKEN)


def api_call(
    method,
    payload=None,
    timeout=None,
):
    if not is_configured():
        raise TelegramError(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

    if not TELEGRAM_URL:
        raise TelegramError(
            "Telegram API URL is not configured."
        )

    request = urllib.request.Request(
        f"{TELEGRAM_URL}/{method}",
        data=json.dumps(
            payload or {}
        ).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=(
                timeout
                or REQUEST_TIMEOUT
            ),
        ) as response:

            raw = response.read().decode(
                "utf-8"
            )

    except urllib.error.HTTPError as error:
        body = error.read().decode(
            "utf-8",
            errors="ignore",
        )

        raise TelegramError(
            f"Telegram HTTP {error.code}: "
            f"{body[:700]}"
        ) from error

    except urllib.error.URLError as error:
        raise TelegramError(
            f"Telegram network error: {error}"
        ) from error

    except Exception as error:
        raise TelegramError(
            f"Telegram request failed: {error}"
        ) from error

    try:
        result = json.loads(raw)

    except json.JSONDecodeError as error:
        raise TelegramError(
            "Telegram returned invalid JSON."
        ) from error

    if not result.get("ok"):
        raise TelegramError(
            result.get(
                "description",
                "Telegram API error.",
            )
        )

    return result


def get_me():
    return api_call("getMe")


def set_webhook(
    webhook_url,
    drop_pending_updates=False,
):
    if not webhook_url:
        raise TelegramError(
            "Webhook URL cannot be empty."
        )

    return api_call(
        "setWebhook",
        {
            "url": webhook_url,
            "drop_pending_updates": (
                drop_pending_updates
            ),
            "allowed_updates": [
                "message"
            ],
        },
    )


def get_webhook_info():
    return api_call(
        "getWebhookInfo"
    )


def delete_webhook(
    drop_pending_updates=False,
):
    return api_call(
        "deleteWebhook",
        {
            "drop_pending_updates": (
                drop_pending_updates
            ),
        },
    )


def send_message(
    chat_id,
    text,
):
    if not text:
        return

    text = str(text)

    limit = TELEGRAM_MESSAGE_LIMIT

    for start in range(
        0,
        len(text),
        limit,
    ):
        chunk = text[
            start:start + limit
        ]

        api_call(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": chunk,
            },
        )


class TelegramBot:
    """
    Telegram API helper for webhook architecture.

    IMPORTANT:
    This class does NOT run getUpdates polling.

    Telegram sends updates directly to the
    Render webhook endpoint.
    """

    def __init__(
        self,
        message_handler=None,
    ):
        self.message_handler = (
            message_handler
        )

        self._running = False

    @property
    def running(self):
        return self._running

    def set_message_handler(
        self,
        handler,
    ):
        self.message_handler = handler

    def process_update(
        self,
        update,
    ):
        if not isinstance(
            update,
            dict,
        ):
            return

        message = update.get(
            "message"
        )

        if not message:
            return

        if not self.message_handler:
            return

        try:
            self.message_handler(
                message
            )

        except Exception as error:

            chat = message.get(
                "chat",
                {},
            )

            chat_id = chat.get(
                "id"
            )

            if chat_id:

                try:
                    send_message(
                        chat_id,
                        (
                            "Agent error:\n"
                            + str(error)[:700]
                        ),
                    )

                except Exception:
                    pass

    def configure_webhook(
        self,
        webhook_url,
    ):
        if not is_configured():
            raise TelegramError(
                "TELEGRAM_BOT_TOKEN "
                "is not configured."
            )

        result = set_webhook(
            webhook_url=webhook_url,
            drop_pending_updates=False,
        )

        self._running = True

        return result

    def webhook_info(self):
        return get_webhook_info()

    def stop(self):
        self._running = False


def create_bot(
    message_handler=None,
):
    return TelegramBot(
        message_handler=message_handler
    )
