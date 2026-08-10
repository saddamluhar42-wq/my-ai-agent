import streamlit as st

from config import APP_NAME, APP_VERSION
from database.models import initialize_database
from telegram.bot import create_bot
from telegram.handlers import create_message_handler
from ui.chat import initialize_chat_state, render_chat
from ui.sidebar import render_sidebar
from ui.styles import get_app_css


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_app():
    initialize_chat_state()

    if "database_initialized" not in st.session_state:
        try:
            initialize_database()

            st.session_state[
                "database_initialized"
            ] = True

            st.session_state[
                "database_error"
            ] = ""

        except Exception as error:
            st.session_state[
                "database_initialized"
            ] = False

            st.session_state[
                "database_error"
            ] = str(error)


def initialize_telegram():
    if "telegram_started" in st.session_state:
        return

    try:
        bot = create_bot(
            message_handler=create_message_handler()
        )

        bot.start(
            background=True
        )

        st.session_state[
            "telegram_bot"
        ] = bot

        st.session_state[
            "telegram_started"
        ] = True

        st.session_state[
            "telegram_error"
        ] = ""

    except Exception as error:
        st.session_state[
            "telegram_started"
        ] = False

        st.session_state[
            "telegram_error"
        ] = str(error)


def render_system_status():
    database_error = st.session_state.get(
        "database_error",
        "",
    )

    telegram_error = st.session_state.get(
        "telegram_error",
        "",
    )

    if database_error:
        st.warning(
            "PostgreSQL is not available. "
            "Chat memory will not work until "
            "DATABASE_URL is configured correctly."
        )

    if telegram_error:
        st.warning(
            "Telegram is not running: "
            + telegram_error
        )


def main():
    st.markdown(
        get_app_css(),
        unsafe_allow_html=True,
    )

    initialize_app()
    initialize_telegram()

    render_sidebar()
    render_system_status()
    render_chat()

    st.caption(
        f"{APP_NAME} v{APP_VERSION}"
    )


if __name__ == "__main__":
    main()
