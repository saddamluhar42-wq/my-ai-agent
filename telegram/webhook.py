import json

from telegram.bot import TelegramError
from telegram.bot import create_bot


def create_webhook_handler(
    message_handler=None,
):
    """
    Create a webhook handler for Telegram updates.

    Telegram sends each update as a JSON object.
    The update is passed to the existing message handler.
    """

    bot = create_bot(
        message_handler=message_handler
    )

    def handle_update(
        update,
    ):
        if not isinstance(
            update,
            dict,
        ):
            raise TelegramError(
                "Invalid Telegram update."
            )

        bot.process_update(
            update
        )

        return {
            "ok": True
        }

    return handle_update


def parse_update(
    request_body,
):
    """
    Convert raw request body into
    a Telegram update dictionary.
    """

    if not request_body:
        raise TelegramError(
            "Empty Telegram webhook request."
        )

    try:

        if isinstance(
            request_body,
            bytes,
        ):
            request_body = (
                request_body.decode(
                    "utf-8"
                )
            )

        if isinstance(
            request_body,
            str,
        ):
            update = json.loads(
                request_body
            )

        elif isinstance(
            request_body,
            dict,
        ):
            update = request_body

        else:
            raise TelegramError(
                "Unsupported webhook body type."
            )

    except json.JSONDecodeError as error:
        raise TelegramError(
            "Telegram webhook sent invalid JSON."
        ) from error

    if not isinstance(
        update,
        dict,
    ):
        raise TelegramError(
            "Telegram update must be a JSON object."
        )

    return update


def process_webhook_request(
    request_body,
    message_handler=None,
):
    """
    Process one Telegram webhook request.
    """

    update = parse_update(
        request_body
    )

    handler = create_webhook_handler(
        message_handler=message_handler
    )

    return handler(
        update
    )
