from ai.agent import (
    AgentError,
    generate,
    generate_image,
    is_image_generation_available,
)

from ai.prompts import build_agent_prompt

from config import (
    MAX_CONVERSATION_MESSAGES,
)

from database.memory import (
    build_memory_context,
    get_recent_messages,
    save_assistant_message,
    save_user_message,
)

from database.models import (
    get_or_create_conversation,
)

from telegram.bot import (
    send_message,
    send_photo,
)


# ============================================================
# IMAGE CONFIRMATION STATE
# ============================================================

_PENDING_IMAGE_REQUESTS = {}


# ============================================================
# USER INFO
# ============================================================

def _get_user_info(message):

    user = message.get(
        "from",
        {},
    )

    telegram_id = user.get(
        "id"
    )

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

        display_name = user.get(
            "username",
            "Telegram User",
        )

    return (
        telegram_id,
        display_name,
    )


# ============================================================
# MESSAGE TEXT
# ============================================================

def _get_message_text(message):

    text = message.get(
        "text"
    )

    if text:

        return text.strip()

    caption = message.get(
        "caption"
    )

    if caption:

        return caption.strip()

    return ""


# ============================================================
# CHAT ID
# ============================================================

def _get_chat_id(message):

    chat = message.get(
        "chat",
        {},
    )

    return chat.get(
        "id"
    )


# ============================================================
# IMAGE REQUEST DETECTION
# ============================================================

def _is_image_request(text):

    if not text:

        return False

    normalized = (
        text.lower()
        .strip()
    )

    image_keywords = [
        "generate image",
        "generate an image",
        "create image",
        "create an image",
        "make image",
        "make an image",
        "draw image",
        "draw an image",
        "image banao",
        "image bana",
        "image generate",
        "image create",
        "tasveer banao",
        "photo banao",
        "picture banao",
        "image chahiye",
        "image bana do",
        "photo bana do",
        "picture bana do",
    ]

    return any(
        keyword in normalized
        for keyword in image_keywords
    )


# ============================================================
# CONFIRMATION DETECTION
# ============================================================

def _is_confirmation(text):

    if not text:

        return False

    normalized = (
        text.lower()
        .strip()
    )

    confirmations = {
        "yes",
        "y",
        "yes please",
        "generate",
        "generate it",
        "go ahead",
        "confirm",
        "confirmed",
        "ok",
        "okay",
        "haan",
        "ha",
        "ji",
        "haan generate karo",
        "banao",
        "bana do",
        "kar do",
        "generate karo",
    }

    return normalized in confirmations


# ============================================================
# CANCEL DETECTION
# ============================================================

def _is_cancellation(text):

    if not text:

        return False

    normalized = (
        text.lower()
        .strip()
    )

    cancellations = {
        "no",
        "n",
        "cancel",
        "cancel it",
        "stop",
        "don't",
        "do not",
        "nah",
        "nahi",
        "nahi chahiye",
        "mat banao",
        "cancel karo",
    }

    return normalized in cancellations


# ============================================================
# START
# ============================================================

def handle_start(
    message,
    user_id,
):

    chat_id = _get_chat_id(
        message
    )

    if not chat_id:

        return

    send_message(
        chat_id,
        (
            "AI Agent ready.\n\n"
            "Aap apna question bhejiye. "
            "Main AI se answer generate karunga.\n\n"
            "Agar image chahiye, "
            "image request bhejiye. "
            "Main generation se pehle "
            "confirmation maangunga."
        ),
    )


# ============================================================
# HELP
# ============================================================

def handle_help(
    message,
    user_id,
):

    chat_id = _get_chat_id(
        message
    )

    if not chat_id:

        return

    send_message(
        chat_id,
        (
            "Available commands:\n\n"
            "/start - Start AI Agent\n"
            "/help - Show help\n"
            "/clear - Start a new conversation\n\n"
            "Normal message bhejkar AI se baat karein.\n\n"
            "Image example:\n"
            "Generate an image of a cute orange cat "
            "in a village garden.\n\n"
            "Image generate karne se pehle "
            "confirmation li jayegi."
        ),
    )


# ============================================================
# CLEAR
# ============================================================

def handle_clear(
    message,
    user_id,
):

    chat_id = _get_chat_id(
        message
    )

    if not chat_id:

        return

    _PENDING_IMAGE_REQUESTS.pop(
        chat_id,
        None,
    )

    get_or_create_conversation(
        user_id,
        title="New Telegram Conversation",
    )

    send_message(
        chat_id,
        (
            "New conversation ready.\n"
            "Aapka next message new context "
            "ke saath process hoga."
        ),
    )


# ============================================================
# IMAGE CONFIRMATION REQUEST
# ============================================================

def _request_image_confirmation(
    chat_id,
    prompt,
):

    _PENDING_IMAGE_REQUESTS[
        chat_id
    ] = prompt

    send_message(
        chat_id,
        (
            "Image generation request detected.\n\n"
            f"Prompt:\n{prompt}\n\n"
            "Kya main image generate karun?\n\n"
            "Reply: Yes / Haan\n"
            "Cancel karne ke liye: No / Nahi"
        ),
    )


# ============================================================
# IMAGE GENERATION
# ============================================================

def _generate_confirmed_image(
    message,
    user_id,
    prompt,
):

    chat_id = _get_chat_id(
        message
    )

    if not chat_id:

        return

    if not is_image_generation_available():

        send_message(
            chat_id,
            (
                "Image generation service "
                "currently configured nahi hai."
            ),
        )

        return

    send_message(
        chat_id,
        "Image generate ho rahi hai...",
    )

    try:

        result = generate_image(
            prompt=prompt,
        )

        image_bytes = result.get(
            "image"
        )

        provider = result.get(
            "provider",
            "Image AI",
        )

        model = result.get(
            "model",
            "",
        )

        if not image_bytes:

            raise AgentError(
                "Image provider returned "
                "an empty image."
            )

        caption = (
            f"Generated by {provider}"
        )

        if model:

            caption += (
                f"\nModel: {model}"
            )

        send_photo(
            chat_id,
            image_bytes,
            caption=caption,
        )

        _PENDING_IMAGE_REQUESTS.pop(
            chat_id,
            None,
        )

    except Exception as error:

        send_message(
            chat_id,
            (
                "Image generation failed:\n"
                f"{str(error)[:1200]}"
            ),
        )


# ============================================================
# AI TEXT MESSAGE
# ============================================================

def handle_ai_message(
    message,
    user_id,
):

    chat_id = _get_chat_id(
        message
    )

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

    # --------------------------------------------------------
    # CHECK PENDING IMAGE CONFIRMATION
    # --------------------------------------------------------

    pending_prompt = (
        _PENDING_IMAGE_REQUESTS.get(
            chat_id
        )
    )

    if pending_prompt:

        if _is_confirmation(
            user_input
        ):

            _generate_confirmed_image(
                message,
                user_id,
                pending_prompt,
            )

            return

        if _is_cancellation(
            user_input
        ):

            _PENDING_IMAGE_REQUESTS.pop(
                chat_id,
                None,
            )

            send_message(
                chat_id,
                "Image generation cancelled.",
            )

            return

        send_message(
            chat_id,
            (
                "Please reply Yes/Haan "
                "to generate the image, "
                "or No/Nahi to cancel."
            ),
        )

        return

    # --------------------------------------------------------
    # NEW IMAGE REQUEST
    # --------------------------------------------------------

    if _is_image_request(
        user_input
    ):

        _request_image_confirmation(
            chat_id,
            user_input,
        )

        return

    # --------------------------------------------------------
    # NORMAL AI CHAT
    # --------------------------------------------------------

    conversation_id = (
        get_or_create_conversation(
            user_id,
            title="Telegram Conversation",
        )
    )

    save_user_message(
        conversation_id,
        user_input,
    )

    recent_messages = (
        get_recent_messages(
            conversation_id,
            limit=MAX_CONVERSATION_MESSAGES,
        )
    )

    memory_context = (
        build_memory_context(
            conversation_id,
            user_input,
        )
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

        error_text = str(
            error
        )

        send_message(
            chat_id,
            (
                "AI Agent error:\n"
                f"{error_text[:1200]}"
            ),
        )


# ============================================================
# MAIN MESSAGE ROUTER
# ============================================================

def handle_message(
    message,
    user_id,
):

    text = _get_message_text(
        message
    )

    command = (
        text.lower()
        .strip()
    )

    if command.startswith(
        "/start"
    ):

        handle_start(
            message,
            user_id,
        )

        return

    if command.startswith(
        "/help"
    ):

        handle_help(
            message,
            user_id,
        )

        return

    if command.startswith(
        "/clear"
    ):

        handle_clear(
            message,
            user_id,
        )

        return

    handle_ai_message(
        message,
        user_id,
    )


# ============================================================
# TELEGRAM MESSAGE HANDLER FACTORY
# ============================================================

def create_message_handler():

    def handler(message):

        telegram_id, display_name = (
            _get_user_info(
                message
            )
        )

        if telegram_id is None:

            return

        from database.models import (
            get_or_create_user,
        )

        user_id = (
            get_or_create_user(
                external_id=(
                    f"telegram:{telegram_id}"
                ),
                display_name=display_name,
            )
        )

        handle_message(
            message,
            user_id,
        )

    return handler
