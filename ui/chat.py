import streamlit as st

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
from files.processor import (
    FileProcessingError,
    build_file_context,
    process_multiple_files,
)


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
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_chat():
    initialize_chat_state()

    render_header()
    render_messages()
    render_uploaded_files()
    render_input_area()


def render_header():
    st.markdown(
        '<div class="main-title">My AI Agent</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-subtitle">'
        "Ask questions, upload files, search the web, "
        "and continue conversations with memory."
        "</div>",
        unsafe_allow_html=True,
    )


def render_messages():
    messages = st.session_state.get(
        "messages",
        [],
    )

    if not messages:
        st.info(
            "Start a conversation by sending a message below."
        )
        return

    for message in messages:
        role = message.get(
            "role",
            "assistant",
        )

        content = message.get(
            "content",
            "",
        )

        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)

        else:
            with st.chat_message("assistant"):
                st.markdown(content)

                provider = message.get(
                    "provider"
                )

                if provider:
                    st.caption(
                        f"Provider: {provider}"
                    )


def render_uploaded_files():
    files = st.session_state.get(
        "uploaded_files",
        [],
    )

    if not files:
        return

    st.markdown(
        "#### Attached files"
    )

    for file_data in files:
        name = file_data.get(
            "name",
            "Unknown file",
        )

        size = file_data.get(
            "size"
        )

        if size:
            size_kb = size / 1024

            st.caption(
                f"📎 {name} — {size_kb:.1f} KB"
            )

        else:
            st.caption(
                f"📎 {name}"
            )


def render_input_area():
    uploaded_files = st.file_uploader(
        "Upload files",
        type=[
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
        ],
        accept_multiple_files=True,
        key="file_uploader",
        label_visibility="collapsed",
    )

    if uploaded_files:
        process_uploads(
            uploaded_files
        )

    prompt = st.chat_input(
        "Message your AI Agent..."
    )

    if prompt:
        handle_user_message(
            prompt
        )


def process_uploads(
    uploaded_files,
):
    current_names = {
        item.get(
            "name"
        )
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


def handle_user_message(
    prompt,
):
    prompt = prompt.strip()

    if not prompt:
        return

    st.session_state[
        "clarification_answer"
    ] = prompt

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

        memory_context = (
            build_memory_context(
                conversation_id,
                prompt,
            )
        )

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

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": answer,
                "provider": provider,
            }
        )

        st.session_state[
            "clarification_question"
        ] = ""

        st.rerun()

    except Exception as error:
        error_message = (
            f"AI Agent error: {error}"
        )

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": error_message,
            }
        )

        st.rerun()


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
