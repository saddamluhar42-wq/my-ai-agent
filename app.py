import streamlit as st

from config import APP_NAME, APP_VERSION
from database.models import initialize_database
from telegram.bot import create_bot
from telegram.handlers import create_message_handler
from ui.chat import initialize_chat_state, render_chat
from ui.sidebar import render_sidebar
from ui.styles import get_app_css

from providers.video.bootstrap import (
    get_video_system_status,
    get_ready_video_providers,
    initialize_video_system,
)

# ============================================================
# STREAMLIT PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# GLOBAL SERVER STATE
# ============================================================

_TELEGRAM_BOT = None
_TELEGRAM_STARTED = False
_TELEGRAM_ERROR = ""

# ============================================================
# DATABASE
# ============================================================


@st.cache_resource
def initialize_server_database():
    """
    Initialize database once per Streamlit server process.
    """

    try:
        initialize_database()
        return True, ""

    except Exception as error:
        return False, str(error)


# ============================================================
# TELEGRAM
# ============================================================


@st.cache_resource
def initialize_server_telegram():
    """
    Start Telegram bot once per Streamlit server process.
    """

    global _TELEGRAM_BOT
    global _TELEGRAM_STARTED
    global _TELEGRAM_ERROR

    if _TELEGRAM_STARTED and _TELEGRAM_BOT is not None:
        return _TELEGRAM_BOT, True, ""

    try:
        handler = create_message_handler()

        bot = create_bot(
            message_handler=handler
        )

        bot.start(
            background=True
        )

        _TELEGRAM_BOT = bot
        _TELEGRAM_STARTED = True
        _TELEGRAM_ERROR = ""

        return bot, True, ""

    except Exception as error:
        _TELEGRAM_BOT = None
        _TELEGRAM_STARTED = False
        _TELEGRAM_ERROR = str(error)

        return None, False, _TELEGRAM_ERROR


# ============================================================
# VIDEO SYSTEM
# ============================================================


@st.cache_resource
def initialize_server_video():
    """
    Initialize the central video-generation system once
    per Streamlit server process.
    """

    try:
        manager = initialize_video_system()
        return manager, True, ""

    except Exception as error:
        return None, False, str(error)


# ============================================================
# APP INITIALIZATION
# ============================================================


def initialize_app():

    initialize_chat_state()

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    database_ok, database_error = (
        initialize_server_database()
    )

    if not database_ok:

        st.session_state[
            "database_initialized"
        ] = False

        st.session_state[
            "database_error"
        ] = database_error

    else:

        st.session_state[
            "database_initialized"
        ] = True

        st.session_state[
            "database_error"
        ] = ""

    # --------------------------------------------------------
    # TELEGRAM
    # --------------------------------------------------------

    bot, telegram_ok, telegram_error = (
        initialize_server_telegram()
    )

    st.session_state[
        "telegram_started"
    ] = telegram_ok

    st.session_state[
        "telegram_error"
    ] = telegram_error

    st.session_state[
        "telegram_bot"
    ] = bot

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    video_manager, video_ok, video_error = (
        initialize_server_video()
    )

    st.session_state[
        "video_system_initialized"
    ] = video_ok

    st.session_state[
        "video_system_error"
    ] = video_error

    st.session_state[
        "video_manager"
    ] = video_manager


# ============================================================
# SYSTEM STATUS
# ============================================================


def render_system_status():

    database_error = st.session_state.get(
        "database_error",
        "",
    )

    telegram_error = st.session_state.get(
        "telegram_error",
        "",
    )

    telegram_started = st.session_state.get(
        "telegram_started",
        False,
    )

    video_error = st.session_state.get(
        "video_system_error",
        "",
    )

    video_initialized = st.session_state.get(
        "video_system_initialized",
        False,
    )

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    if database_error:

        st.warning(
            "PostgreSQL is not available. "
            "Chat memory will not work until "
            "DATABASE_URL is configured correctly."
        )

    # --------------------------------------------------------
    # TELEGRAM
    # --------------------------------------------------------

    if telegram_error:

        st.warning(
            "Telegram is not running: "
            + telegram_error
        )

    elif telegram_started:

        st.caption(
            "Telegram Bot: Connected"
        )

    # --------------------------------------------------------
    # VIDEO SYSTEM
    # --------------------------------------------------------

    if video_error:

        st.warning(
            "Video system initialization failed: "
            + video_error
        )

        return

    if not video_initialized:

        st.warning(
            "Video system is not initialized."
        )

        return

    try:

        status = get_video_system_status()

        ready_providers = (
            get_ready_video_providers()
        )

        provider_count = len(
            ready_providers
        )

        st.caption(
            f"Video Providers: {provider_count} Ready"
        )

        with st.expander(
            "Video Provider Status",
            expanded=False,
        ):

            providers = status.get(
                "providers",
                {},
            )

            if not providers:

                st.info(
                    "No video providers are registered."
                )

            else:

                for name, data in providers.items():

                    available = bool(
                        data.get(
                            "available",
                            False,
                        )
                    )

                    configured = bool(
                        data.get(
                            "configured",
                            False,
                        )
                    )

                    enabled = bool(
                        data.get(
                            "enabled",
                            False,
                        )
                    )

                    if available:

                        state = "Connected"

                    elif not enabled:

                        state = "Disabled"

                    elif not configured:

                        state = "Not configured"

                    else:

                        state = "Unavailable"

                    st.write(
                        f"**{name}** — {state}"
                    )

    except Exception as error:

        st.warning(
            "Unable to read video provider status: "
            + str(error)
        )


# ============================================================
# MAIN
# ============================================================


def main():

    st.markdown(
        get_app_css(),
        unsafe_allow_html=True,
    )

    # Server-level initialization
    initialize_app()

    render_sidebar()

    render_system_status()

    render_chat()

    st.caption(
        f"{APP_NAME} v{APP_VERSION}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
