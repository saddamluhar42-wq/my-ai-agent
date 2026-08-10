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
    build_file_context,
    process_multiple_files,
)


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

    render_messages()
    render_composer()


def render_messages():
    messages = st.session_state.get(
        "messages",
        [],
    )

    if not messages:
        render_empty_state()
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

        with st.chat_message(role):
            st.markdown(content)

            provider = message.get(
                "provider"
            )

            if provider:
                st.caption(
                    f"Powered by {provider}"
                )


def render_empty_state():
    st.markdown(
        """
        <div class="welcome-container">
            <div class="welcome-icon">✦</div>
            <div class="welcome-title">
                How can I help you today?
            </div>
            <div class="welcome-subtitle">
                Ask anything or attach a file
                using the + button below.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    joined_names = ", ".join(names)

    return (
        "Please analyze these attached "
        f"files: {joined_names}"
    )


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
        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": (
                    f"AI Agent error: {error}"
                ),
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
