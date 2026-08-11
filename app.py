import streamlit as st

from config import APP_NAME, APP_VERSION
from database.models import initialize_database
from telegram.bot import create_bot
from telegram.handlers import create_message_handler
from ui.chat import initialize_chat_state, render_chat
from ui.sidebar import render_sidebar
from ui.styles import get_app_css
from ui.knowledge_manager import render_knowledge_manager
from knowledge.document_rag import install_core_bridge

from providers.video.bootstrap import (
    get_video_system_status,
    get_ready_video_providers,
    initialize_video_system,
)

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

_TELEGRAM_BOT = None
_TELEGRAM_STARTED = False
_TELEGRAM_ERROR = ""


@st.cache_resource
def initialize_server_database():
    try:
        initialize_database()
        return True, ""
    except Exception as error:
        return False, str(error)


@st.cache_resource
def initialize_server_telegram():
    global _TELEGRAM_BOT, _TELEGRAM_STARTED, _TELEGRAM_ERROR
    if _TELEGRAM_STARTED and _TELEGRAM_BOT is not None:
        return _TELEGRAM_BOT, True, ""
    try:
        handler = create_message_handler()
        bot = create_bot(message_handler=handler)
        bot.start(background=True)
        _TELEGRAM_BOT = bot
        _TELEGRAM_STARTED = True
        _TELEGRAM_ERROR = ""
        return bot, True, ""
    except Exception as error:
        _TELEGRAM_BOT = None
        _TELEGRAM_STARTED = False
        _TELEGRAM_ERROR = str(error)
        return None, False, _TELEGRAM_ERROR


@st.cache_resource
def initialize_server_video():
    try:
        manager = initialize_video_system()
        return manager, True, ""
    except Exception as error:
        return None, False, str(error)


def initialize_app():
    initialize_chat_state()

    database_ok, database_error = initialize_server_database()
    st.session_state["database_initialized"] = database_ok
    st.session_state["database_error"] = database_error

    bot, telegram_ok, telegram_error = initialize_server_telegram()
    st.session_state["telegram_started"] = telegram_ok
    st.session_state["telegram_error"] = telegram_error
    st.session_state["telegram_bot"] = bot

    video_manager, video_ok, video_error = initialize_server_video()
    st.session_state["video_system_initialized"] = video_ok
    st.session_state["video_system_error"] = video_error
    st.session_state["video_manager"] = video_manager

    # Install document RAG before chat requests are processed.
    install_core_bridge()


def render_system_status():
    database_error = st.session_state.get("database_error", "")
    telegram_error = st.session_state.get("telegram_error", "")
    telegram_started = st.session_state.get("telegram_started", False)
    video_error = st.session_state.get("video_system_error", "")
    video_initialized = st.session_state.get("video_system_initialized", False)

    if database_error:
        st.warning("PostgreSQL is not available. Chat memory will not work until DATABASE_URL is configured correctly.")

    if telegram_error:
        st.warning("Telegram is not running: " + telegram_error)
    elif telegram_started:
        st.caption("Telegram Bot: Connected")

    if video_error:
        st.warning("Video system initialization failed: " + video_error)
        return

    if not video_initialized:
        st.warning("Video system is not initialized.")
        return

    try:
        status = get_video_system_status()
        ready_providers = get_ready_video_providers()
        st.caption(f"Video Providers: {len(ready_providers)} Ready")

        with st.expander("Video Provider Status", expanded=False):
            providers = status.get("providers", {})
            if not providers:
                st.info("No video providers are registered.")
            else:
                for name, data in providers.items():
                    available = bool(data.get("available", False))
                    configured = bool(data.get("configured", False))
                    enabled = bool(data.get("enabled", False))
                    if available:
                        state = "Connected"
                    elif not enabled:
                        state = "Disabled"
                    elif not configured:
                        state = "Not configured"
                    else:
                        state = "Unavailable"
                    st.write(f"**{name}** — {state}")
    except Exception as error:
        st.warning("Unable to read video provider status: " + str(error))


def main():
    st.markdown(get_app_css(), unsafe_allow_html=True)
    initialize_app()
    render_sidebar()
    render_knowledge_manager()
    render_system_status()
    render_chat()
    st.caption(f"{APP_NAME} v{APP_VERSION}")


if __name__ == "__main__":
    main()
