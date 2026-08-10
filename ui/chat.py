import streamlit as st

from ai.agent import (
    AgentError,
    generate,
    generate_image,
    is_image_generation_available,
)
from ai.prompts import build_agent_prompt
from config import MAX_CONVERSATION_MESSAGES
from database.memory import (
    build_memory_context,
    get_recent_messages,
    save_assistant_message,
    save_user_message,
)
from database.models import get_or_create_conversation
from files.processor import (
    build_file_context,
    process_multiple_files,
)


# ============================================================
# FILE SUPPORT
# ============================================================

ALLOWED_FILE_TYPES = [
    "txt",
    "md",
    "csv",
    "json",
    "py",
    "html",
    "xml",
    "yaml",
    "yml",
    "pdf",
    "docx",
]


# ============================================================
# IMAGE REQUEST DETECTION
# ============================================================

IMAGE_REQUEST_PHRASES = [
    "generate image",
    "create image",
    "make image",
    "generate an image",
    "generate a image",
    "create an image",
    "create a image",
    "make an image",
    "make a image",
    "image generate",
    "image banao",
    "image bana",
    "image bana do",
    "photo banao",
    "photo bana do",
    "picture banao",
    "picture bana do",
    "tasveer banao",
    "tasveer bana do",
    "image generate karo",
    "image create karo",
    "image bana do",
    "image chahiye",
]


YES_WORDS = [
    "yes",
    "y",
    "haan",
    "ha",
    "ji",
    "ji haan",
    "kar do",
    "bana do",
    "generate karo",
    "generate",
    "proceed",
    "ok",
    "okay",
]


NO_WORDS = [
    "no",
    "n",
    "nahi",
    "nahin",
    "cancel",
    "cancel karo",
    "mat karo",
    "stop",
]


# ============================================================
# STATE
# ============================================================

def initialize_chat_state():

    defaults = {
        "messages": [],
        "uploaded_files": [],
        "file_context": "",
        "clarification_answer": "",
        "clarification_question": "",
        "conversation_id": None,
        "user_id": None,
        "preferred_provider": "Auto",
        "pending_image_prompt": None,
        "show_provider_info": True,
        "enable_chat_memory": True,
        "confirm_image_generation": True,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# MAIN CHAT
# ============================================================

def render_chat():

    initialize_chat_state()

    render_chat_header()

    if not st.session_state.get("messages"):

        render_empty_state()

    else:

        render_messages()

    render_composer()


# ============================================================
# CHAT HEADER
# ============================================================

def render_chat_header():

    provider = st.session_state.get(
        "preferred_provider",
        "Auto",
    )

    provider_text = provider

    st.markdown(
        f"""
<div class="chat-header">
    <div>
        My AI Agent
        <span style="
            color:#858585;
            font-weight:400;
            margin-left:8px;
        ">
            {provider_text}
        </span>
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# EMPTY STATE
# ============================================================

def render_empty_state():

    st.markdown(
        """
<div class="empty-state">
    <div class="empty-state-icon">
        ✦
    </div>

    <div class="empty-state-title">
        How can I help you today?
    </div>

    <div class="empty-state-subtitle">
        Ask anything, upload a file, or request an image.
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div style="
    width:min(820px,92%);
    margin:38px auto 0 auto;
">
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(
        3,
        gap="small",
    )

    with col1:

        if st.button(
            "Explain something",
            use_container_width=True,
            key="suggest_explain",
        ):

            handle_user_message(
                "Explain something interesting to me."
            )

    with col2:

        if st.button(
            "Write something",
            use_container_width=True,
            key="suggest_write",
        ):

            handle_user_message(
                "Help me write something useful."
            )

    with col3:

        if st.button(
            "Generate an image",
            use_container_width=True,
            key="suggest_image",
        ):

            handle_user_message(
                "Generate an image of a beautiful cinematic landscape."
            )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# MESSAGE RENDERING
# ============================================================

def render_messages():

    messages = st.session_state.get(
        "messages",
        [],
    )

    for message_index, message in enumerate(messages):

        role = message.get(
            "role",
            "assistant",
        )

        content = message.get(
            "content",
            "",
        )

        message_type = message.get(
            "type",
            "text",
        )

        with st.chat_message(role):

            if message_type == "image":

                render_image_message(
                    message,
                    message_index,
                )

                continue

            if content:

                st.markdown(content)

            if (
                role == "assistant"
                and st.session_state.get(
                    "show_provider_info",
                    True,
                )
            ):

                provider = message.get(
                    "provider",
                )

                if provider:

                    model = message.get(
                        "model",
                    )

                    if model:

                        st.caption(
                            f"{provider} • {model}"
                        )

                    else:

                        st.caption(
                            f"Powered by {provider}"
                        )


# ============================================================
# IMAGE MESSAGE
# ============================================================

def render_image_message(
    message,
    message_index,
):

    image_data = message.get(
        "image",
    )

    if not image_data:
        return

    st.image(
        image_data,
        use_container_width=True,
    )

    st.download_button(
        label="Download image",
        data=image_data,
        file_name=(
            f"my_ai_agent_image_"
            f"{message_index}.png"
        ),
        mime="image/png",
        key=(
            f"download_image_"
            f"{message_index}"
        ),
    )

    provider = message.get(
        "provider",
    )

    model = message.get(
        "model",
    )

    if provider:

        if model:

            st.caption(
                f"Generated by {provider} • {model}"
            )

        else:

            st.caption(
                f"Generated by {provider}"
            )


# ============================================================
# COMPOSER
# ============================================================

def render_composer():

    submission = st.chat_input(
        "Message My AI Agent...",
        accept_file="multiple",
        file_type=ALLOWED_FILE_TYPES,
        max_upload_size=200,
        key="main_chat_input",
    )

    if submission is None:
        return

    text = submission.text.strip()

    files = list(
        submission.files
    )

    if files:

        process_uploaded_files(
            files
        )

    if not text and files:

        text = build_file_message(
            files
        )

    if text:

        handle_user_message(
            text
        )


# ============================================================
# FILE MESSAGE
# ============================================================

def build_file_message(files):

    names = [
        file.name
        for file in files
    ]

    if len(names) == 1:

        return (
            "Please analyze the attached "
            f"file: {names[0]}"
        )

    joined_names = ", ".join(
        names
    )

    return (
        "Please analyze these attached "
        f"files: {joined_names}"
    )


# ============================================================
# FILE PROCESSING
# ============================================================

def process_uploaded_files(
    uploaded_files,
):

    current_names = {
        item.get("name")
        for item in st.session_state.get(
            "uploaded_files",
            [],
        )
    }

    new_files = [
        file
        for file in uploaded_files
        if file.name not in current_names
    ]

    if not new_files:
        return

    processed, errors = (
        process_multiple_files(
            new_files
        )
    )

    if processed:

        existing = st.session_state.get(
            "uploaded_files",
            [],
        )

        existing.extend(
            processed
        )

        st.session_state[
            "uploaded_files"
        ] = existing

        st.session_state[
            "file_context"
        ] = build_file_context(
            existing
        )

    for error in errors:

        st.warning(
            f"{error['name']}: "
            f"{error['error']}"
        )


# ============================================================
# IMAGE REQUEST
# ============================================================

def is_image_request(prompt):

    text = prompt.lower().strip()

    for phrase in IMAGE_REQUEST_PHRASES:

        if phrase in text:
            return True

    return False


# ============================================================
# CONFIRMATION
# ============================================================

def is_yes_confirmation(prompt):

    return (
        prompt.lower().strip()
        in YES_WORDS
    )


def is_no_confirmation(prompt):

    return (
        prompt.lower().strip()
        in NO_WORDS
    )


def request_image_confirmation(
    image_prompt,
):

    st.session_state[
        "pending_image_prompt"
    ] = image_prompt

    st.session_state[
        "messages"
    ].append(
        {
            "role": "assistant",
            "content": (
                "I detected an image-generation "
                "request.\n\n"
                "Should I generate this image?\n\n"
                "**Yes / No**"
            ),
        }
    )

    st.rerun()


# ============================================================
# PENDING IMAGE CONFIRMATION
# ============================================================

def handle_pending_image_confirmation(
    prompt,
):

    pending_prompt = (
        st.session_state.get(
            "pending_image_prompt"
        )
    )

    if not pending_prompt:
        return False

    if is_yes_confirmation(prompt):

        st.session_state[
            "pending_image_prompt"
        ] = None

        st.session_state[
            "messages"
        ].append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        generate_confirmed_image(
            pending_prompt
        )

        return True

    if is_no_confirmation(prompt):

        st.session_state[
            "pending_image_prompt"
        ] = None

        st.session_state[
            "messages"
        ].append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": (
                    "Image generation cancelled."
                ),
            }
        )

        st.rerun()

        return True

    st.session_state[
        "messages"
    ].append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    st.session_state[
        "messages"
    ].append(
        {
            "role": "assistant",
            "content": (
                "Please confirm with **Yes** "
                "or **No**."
            ),
        }
    )

    st.rerun()

    return True


# ============================================================
# IMAGE GENERATION
# ============================================================

def generate_confirmed_image(
    image_prompt,
):

    try:

        if not is_image_generation_available():

            raise AgentError(
                "No image-generation provider "
                "is configured."
            )

        ensure_database_context()

        conversation_id = (
            st.session_state[
                "conversation_id"
            ]
        )

        save_user_message(
            conversation_id,
            "Image generation confirmed: "
            + image_prompt,
        )

        with st.spinner(
            "Generating image..."
        ):

            result = generate_image(
                prompt=image_prompt,
            )

        image_data = result.get(
            "image",
        )

        if not image_data:

            raise AgentError(
                "Image generation returned "
                "no image."
            )

        provider = result.get(
            "provider",
            "Unknown",
        )

        model = result.get(
            "model",
            "",
        )

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": "",
                "type": "image",
                "image": image_data,
                "provider": provider,
                "model": model,
            }
        )

        save_assistant_message(
            conversation_id,
            "[Image generated]",
            provider=provider,
        )

        st.rerun()

    except Exception as error:

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": (
                    "Image generation failed:\n\n"
                    f"{error}"
                ),
            }
        )

        st.rerun()


# ============================================================
# USER MESSAGE HANDLER
# ============================================================

def handle_user_message(
    prompt,
):

    prompt = prompt.strip()

    if not prompt:
        return

    st.session_state[
        "clarification_answer"
    ] = prompt

    # --------------------------------------------------------
    # PENDING IMAGE CONFIRMATION
    # --------------------------------------------------------

    if st.session_state.get(
        "pending_image_prompt"
    ):

        handle_pending_image_confirmation(
            prompt
        )

        return

    # --------------------------------------------------------
    # IMAGE REQUEST
    # --------------------------------------------------------

    if is_image_request(prompt):

        st.session_state[
            "messages"
        ].append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        request_image_confirmation(
            prompt
        )

        return

    # --------------------------------------------------------
    # NORMAL TEXT CHAT
    # --------------------------------------------------------

    st.session_state[
        "messages"
    ].append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    try:

        ensure_database_context()

        conversation_id = (
            st.session_state[
                "conversation_id"
            ]
        )

        save_user_message(
            conversation_id,
            prompt,
        )

        recent_messages = (
            get_recent_messages(
                conversation_id,
                limit=MAX_CONVERSATION_MESSAGES,
            )
        )

        if st.session_state.get(
            "enable_chat_memory",
            True,
        ):

            memory_context = (
                build_memory_context(
                    conversation_id,
                    prompt,
                )
            )

        else:

            memory_context = ""

        file_context = (
            st.session_state.get(
                "file_context",
                "",
            )
        )

        preferred_provider = (
            st.session_state.get(
                "preferred_provider",
                "Auto",
            )
        )

        if preferred_provider == "Auto":

            preferred_provider = None

        agent_prompt = (
            build_agent_prompt(
                user_input=prompt,
                messages=recent_messages,
                memory_context=memory_context,
                file_context=file_context,
            )
        )

        with st.spinner(
            "Thinking..."
        ):

            result = generate(
                prompt=agent_prompt,
                preferred_provider=preferred_provider,
            )

        answer = result.get(
            "answer",
            "",
        )

        provider = result.get(
            "provider",
        )

        model = result.get(
            "model",
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

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": answer,
                "provider": provider,
                "model": model,
            }
        )

        st.session_state[
            "clarification_question"
        ] = ""

        st.rerun()

    except Exception as error:

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": (
                    "AI Agent error:\n\n"
                    f"{error}"
                ),
            }
        )

        st.rerun()


# ============================================================
# DATABASE CONTEXT
# ============================================================

def ensure_database_context():

    if st.session_state.get(
        "user_id"
    ) is None:

        from database.models import (
            get_or_create_user,
        )

        user_id = get_or_create_user(
            external_id="streamlit:web-user",
            display_name="Web User",
        )

        st.session_state[
            "user_id"
        ] = user_id

    if st.session_state.get(
        "conversation_id"
    ) is None:

        conversation_id = (
            get_or_create_conversation(
                st.session_state[
                    "user_id"
                ],
                title="Web Conversation",
            )
        )

        st.session_state[
            "conversation_id"
        ] = conversation_id
