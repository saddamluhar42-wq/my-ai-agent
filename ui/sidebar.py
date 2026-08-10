import streamlit as st

from config import (
    APP_NAME,
    APP_VERSION,
    get_config_status,
)


def render_sidebar():
    with st.sidebar:
        st.markdown(
            f"## {APP_NAME}"
        )

        st.caption(
            f"Version {APP_VERSION}"
        )

        st.divider()

        st.subheader("Agent")

        status = get_config_status()

        if status["gemini"]:
            st.success(
                "Gemini: Connected"
            )
        else:
            st.warning(
                "Gemini: Not configured"
            )

        if status["openrouter"]:
            st.success(
                "OpenRouter: Connected"
            )
        else:
            st.warning(
                "OpenRouter: Not configured"
            )

        if status["tavily"]:
            st.success(
                "Tavily: Connected"
            )
        else:
            st.info(
                "Tavily: Not configured"
            )

        if status["database"]:
            st.success(
                "PostgreSQL: Connected"
            )
        else:
            st.warning(
                "PostgreSQL: Not configured"
            )

        if status["telegram"]:
            st.success(
                "Telegram: Configured"
            )
        else:
            st.info(
                "Telegram: Not configured"
            )

        st.divider()

        st.subheader("Conversation")

        if st.button(
            "＋ New Chat",
            use_container_width=True,
        ):
            _reset_chat()

        if st.button(
            "Clear Current Chat",
            use_container_width=True,
        ):
            _clear_messages()

        st.divider()

        st.subheader("Settings")

        provider = st.selectbox(
            "Preferred AI Provider",
            [
                "Auto",
                "Gemini",
                "OpenRouter",
            ],
            key="preferred_provider",
        )

        st.session_state[
            "preferred_provider"
        ] = provider

        st.divider()

        st.caption(
            "AI Agent • Streamlit • PostgreSQL"
        )


def _reset_chat():
    st.session_state[
        "messages"
    ] = []

    st.session_state[
        "uploaded_files"
    ] = []

    st.session_state[
        "file_context"
    ] = ""

    st.session_state[
        "clarification_answer"
    ] = ""

    st.session_state[
        "clarification_question"
    ] = ""

    st.rerun()


def _clear_messages():
    st.session_state[
        "messages"
    ] = []

    st.session_state[
        "clarification_answer"
    ] = ""

    st.session_state[
        "clarification_question"
    ] = ""

    st.rerun()
