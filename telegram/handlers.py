from ai.agent import AgentError, generate
from ai.prompts import build_agent_prompt
from config import MAX_CONVERSATION_MESSAGES
from database.memory import (
    build_memory_context,
    get_recent_messages,
    save_assistant_message,
    save_user_message,
)
from database.models import get_or_create_conversation
from telegram.bot import send_message


def _get_user_info(message):
    user = message.get("from", {})

    telegram_id = user.get("id")

    first_name = user.get(
        "first_name",
        "",
    )

    last_name = user.get(
        "last_name",
        "",
    )

    display_name = (
        f"{first_name} {last_name}"
    ).strip()

    if not display_name:
        display_name = (
            user.get(
                "username",
                "Telegram User",
            )
        )

    return telegram_id, display_name


def _get_message_text(message):
    text = message.get("text")

    if text:
        return text.strip()

    caption = message.get("caption")

    if caption:
        return caption.strip()

    return ""


def handle_start(
    message,
    user_id,
):
    chat = message.get(
        "chat",
        {},
    )

    chat_id = chat.get("id")

    if not chat_id:
        return

    send_message(
        chat_id,
        (
            "AI Agent ready.\n\n"
            "Aap apna question bhejiye. "
            "Main AI se answer generate karunga."
        ),
    )


def handle_help(
    message,
    user_id,
):
    chat = message.get(
        "chat",
        {},
    )

    chat_id = chat.get("id")

    if not chat_id:
        return

    send_message(
        chat_id,
        (
            "Available commands:\n\n"
            "/start - Start AI Agent\n"
            "/help - Show help\n"
            "/clear - Start a new conversation\n\n"
            "Normal message bhejkar AI se baat karein."
        ),
    )


def handle_clear(
    message,
    user_id,
):
    chat = message.get(
        "chat",
        {},
    )

    chat_id = chat.get("id")

    if not chat_id:
        return

    conversation_id = get_or_create_conversation(
        user_id,
        title="New Telegram Conversation",
    )

    send_message(
        chat_id,
        (
            "New conversation ready.\n"
            "Aapka next message new context ke saath process hoga."
        ),
    )


def handle_ai_message(
    message,
    user_id,
):
    chat = message.get(
        "chat",
        {},
    )

    chat_id = chat.get("id")

    if not chat_id:
        return

    user_input = _get_message_text(
        message
    )

    if not user_input:
        send_message(
            chat_id,
            (
                "Abhi main text messages process "
                "kar raha hoon. Please text bhejiye."
            ),
        )
        return

    conversation_id = get_or_create_conversation(
        user_id,
        title="Telegram Conversation",
    )

    save_user_message(
        conversation_id,
        user_input,
    )

    recent_messages = get_recent_messages(
        conversation_id,
        limit=MAX_CONVERSATION_MESSAGES,
    )

    memory_context = build_memory_context(
        conversation_id,
        user_input,
    )

    prompt = build_agent_prompt(
        user_input=user_input,
        messages=recent_messages,
        memory_context=memory_context,
    )

    try:
        result = generate(
            prompt=prompt
        )

        answer = result.get(
            "answer",
            "",
        )

        provider = result.get(
            "provider"
        )

        if not answer:
            raise AgentError(
                "AI returned an empty response."
            )

        save_assistant_message(
            conversation_id,
            answer,
            provider=provider,
        )

        send_message(
            chat_id,
            answer,
        )

    except Exception as error:
        error_text = str(error)

        send_message(
            chat_id,
            (
                "AI Agent error:\n"
                f"{error_text[:1200]}"
            ),
        )


def handle_message(
    message,
    user_id,
):
    text = _get_message_text(
        message
    )

    if text.startswith("/start"):
        handle_start(
            message,
            user_id,
        )
        return

    if text.startswith("/help"):
        handle_help(
            message,
            user_id,
        )
        return

    if text.startswith("/clear"):
        handle_clear(
            message,
            user_id,
        )
        return

    handle_ai_message(
        message,
        user_id,
    )


def create_message_handler():
    def handler(message):
        telegram_id, display_name = (
            _get_user_info(message)
        )

        if telegram_id is None:
            return

        from database.models import (
            get_or_create_user,
        )

        user_id = get_or_create_user(
            external_id=f"telegram:{telegram_id}",
            display_name=display_name,
        )

        handle_message(
            message,
            user_id,
        )

    return handler
