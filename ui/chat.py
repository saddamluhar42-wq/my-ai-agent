import streamlit as st

from agent.core import run_agent
from ai.agent import (
    AgentError,
    generate_image,
    is_image_generation_available,
)
from database.memory import (
    build_memory_context,
    get_recent_messages,
    save_assistant_message,
    save_user_message,
)
from database.models import (
    get_or_create_conversation,
    get_or_create_user,
)
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
# EMPTY STATE IMAGE
# ============================================================

EMPTY_STATE_IMAGE = "assets/agent_astronaut.webp"


# ============================================================
# IMAGE REQUEST DETECTION
# ============================================================

IMAGE_REQUEST_PHRASES = [
    "generate image",
    "create image",
    "make image",
    "generate an image",
    "create an image",
    "make an image",
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


# ============================================================
# IMAGE CONFIRMATION
# ============================================================

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
# CHAT STATE
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
            {provider}
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
        "<div style='height:55px'></div>",
        unsafe_allow_html=True,
    )

    image_col_left, image_col, image_col_right = st.columns(
        [1, 1, 1]
    )

    with image_col:

        try:

            st.image(
                EMPTY_STATE_IMAGE,
                width=155,
            )

        except Exception:

            st.markdown(
                """
                <div style="
                    text-align:center;
                    font-size:48px;
                    padding:30px;
                ">
                    🤖
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div style="
            text-align:center;
            margin-top:8px;
            margin-bottom:8px;
        ">
            <div style="
                font-size:28px;
                font-weight:600;
                color:#f5f5f5;
            ">
                How can I help you today?
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            text-align:center;
            color:#9b9b9b;
            font-size:14px;
            line-height:1.6;
            margin-bottom:30px;
        ">
            Ask anything, upload a file, or request an image.
        </div>
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

                st.markdown(
                    content
                )

            if (
                role == "assistant"
                and st.session_state.get(
                    "show_provider_info",
                    True,
                )
            ):

                provider = message.get(
                    "provider"
                )

                model = message.get(
                    "model"
                )

                if provider:

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
        "image"
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
        "provider"
    )

    model = message.get(
        "model"
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
# IMAGE REQUEST DETECTION
# ============================================================

def is_image_request(prompt):

    text = prompt.lower().strip()

    return any(
        phrase in text
        for phrase in IMAGE_REQUEST_PHRASES
    )


# ============================================================
# IMAGE CONFIRMATION
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
# CONFIRMED IMAGE GENERATION
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
# USER MESSAGE
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
    # NORMAL AI CHAT
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

        user_id = (
            st.session_state[
                "user_id"
            ]
        )

        save_user_message(
            conversation_id,
            prompt,
        )

        recent_messages = (
            get_recent_messages(
                conversation_id,
                limit=30,
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

        # ----------------------------------------------------
        # AGENT CORE
        # ----------------------------------------------------

        context = {
            "user_id": user_id,
            "memory_context": memory_context,
            "file_context": file_context,
            "recent_messages": recent_messages,
            "preferred_provider": preferred_provider,
            "uploaded_files": (
                st.session_state.get(
                    "uploaded_files",
                    [],
                )
            ),
        }

        with st.spinner(
            "Thinking..."
        ):

            result = run_agent(
                query=prompt,
                context=context,
            )

        if not result.success:

            error_message = result.metadata.get(
                "error",
                "Agent execution failed.",
            )

            raise AgentError(
                error_message
            )

        answer = result.answer

        provider = result.provider

        metadata = result.metadata or {}

        model = metadata.get(
            "model",
            "",
        )

        if not answer:

            raise AgentError(
                "Agent returned an empty response."
            )

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        save_assistant_message(
            conversation_id,
            answer,
            provider=provider,
        )

        # ----------------------------------------------------
        # UI
        # ----------------------------------------------------

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": answer,
                "provider": provider,
                "model": model,
                "type": "text",
                "skill": metadata.get(
                    "primary_skill",
                    "",
                ),
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
                "type": "text",
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
