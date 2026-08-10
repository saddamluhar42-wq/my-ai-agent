import json
import threading
import time
import urllib.error
import urllib.request

from config import (
    REQUEST_TIMEOUT,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_MESSAGE_LIMIT,
    TELEGRAM_POLL_TIMEOUT,
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
            f"Telegram network error: "
            f"{error}"
        ) from error

    except Exception as error:
        raise TelegramError(
            f"Telegram request failed: "
            f"{error}"
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
    return api_call(
        "getMe"
    )


def get_updates(
    offset=None,
):
    payload = {
        "timeout": TELEGRAM_POLL_TIMEOUT,
        "allowed_updates": [
            "message"
        ],
    }

    if offset is not None:
        payload["offset"] = offset

    result = api_call(
        "getUpdates",
        payload,
        timeout=(
            TELEGRAM_POLL_TIMEOUT
            + 15
        ),
    )

    return result.get(
        "result",
        [],
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


def delete_webhook():
    return api_call(
        "deleteWebhook",
        {
            "drop_pending_updates": False,
        },
    )


class TelegramBot:
    def __init__(
        self,
        message_handler=None,
    ):
        self.message_handler = (
            message_handler
        )

        self._thread = None
        self._stop_event = (
            threading.Event()
        )

        self._offset = None
        self._running = False

    @property
    def running(self):
        return self._running

    def set_message_handler(
        self,
        handler,
    ):
        self.message_handler = handler

    def stop(self):
        self._stop_event.set()
        self._running = False

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
                        "Agent error:\n"
                        + str(error)[:700],
                    )

                except Exception:
                    pass

    def poll_once(self):
        updates = get_updates(
            offset=self._offset
        )

        for update in updates:
            update_id = update.get(
                "update_id"
            )

            if update_id is not None:
                self._offset = (
                    update_id + 1
                )

            self.process_update(
                update
            )

    def _poll_loop(self):
        self._running = True

        while not self._stop_event.is_set():
            try:
                self.poll_once()

            except Exception:
                if self._stop_event.wait(5):
                    break

        self._running = False

    def start(
        self,
        background=True,
    ):
        if not is_configured():
            raise TelegramError(
                "TELEGRAM_BOT_TOKEN "
                "is not configured."
            )

        # Polling requires webhook mode
        # to be disabled.
        delete_webhook()

        if not background:
            self._poll_loop()
            return

        if (
            self._thread
            and self._thread.is_alive()
        ):
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._poll_loop,
            name="telegram-bot",
            daemon=True,
        )

        self._thread.start()


def create_bot(
    message_handler=None,
):
    return TelegramBot(
        message_handler=message_handler
    )
