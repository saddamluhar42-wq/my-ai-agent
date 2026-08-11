import streamlit as st

from config import (
    APP_NAME,
    APP_VERSION,
    get_config_status,
)


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():

    with st.sidebar:

        render_brand()

        if st.button(
            "＋  New chat",
            use_container_width=True,
            type="primary",
            key="sidebar_new_chat",
        ):
            _reset_chat()

        st.text_input(
            "Search",
            placeholder="Search conversations...",
            label_visibility="collapsed",
            key="chat_search_query",
        )

        st.divider()

        render_conversation_section()

        st.divider()

        render_ai_section()

        st.divider()

        render_services_section()

        st.divider()

        render_current_chat_section()

        st.divider()

        render_settings_section()

        render_footer()


# ============================================================
# BRAND
# ============================================================

def render_brand():

    col1, col2 = st.columns(
        [0.22, 0.78],
        vertical_alignment="center",
    )

    with col1:
        st.markdown("### 🤖")

    with col2:
        st.markdown(
            f"**{APP_NAME}**"
        )

        st.caption(
            f"v{APP_VERSION}"
        )


# ============================================================
# CONVERSATIONS
# ============================================================

def render_conversation_section():

    st.markdown("**Recent chats**")

    messages = st.session_state.get(
        "messages",
        [],
    )

    if not messages:
        st.caption("No conversations yet.")
        return

    user_messages = [
        message
        for message in messages
        if message.get("role") == "user"
    ]

    if user_messages:

        latest = user_messages[-1].get(
            "content",
            "",
        )

        if latest:

            title = latest.strip()

            if len(title) > 34:
                title = (
                    title[:34].rstrip()
                    + "..."
                )

            if st.button(
                f"💬  {title}",
                use_container_width=True,
                key="current_conversation_button",
            ):
                st.session_state[
                    "scroll_to_bottom"
                ] = True

    else:
        st.caption("Current chat")


# ============================================================
# AI PROVIDERS
# ============================================================

def render_ai_section():

    st.markdown("**AI model**")

    provider_options = [
        "Auto",
        "Gemini",
        "OpenRouter",
        "Groq",
        "Cerebras",
        "Mistral",
        "Anthropic",
    ]

    current_provider = st.session_state.get(
        "preferred_provider",
        "Auto",
    )

    if current_provider not in provider_options:
        current_provider = "Auto"

        st.session_state[
            "preferred_provider"
        ] = "Auto"

    st.selectbox(
        "Provider",
        provider_options,
        index=provider_options.index(
            current_provider
        ),
        key="preferred_provider",
        label_visibility="collapsed",
    )

    selected = st.session_state.get(
        "preferred_provider",
        "Auto",
    )

    if selected == "Auto":
        st.caption(
            "Automatic provider selection"
        )

    else:
        st.caption(
            f"Using {selected}"
        )


# ============================================================
# SERVICES
# ============================================================

def render_services_section():

    st.markdown("**Services**")

    status = get_config_status()

    render_status_row(
        "Gemini",
        status.get("gemini", False),
    )

    render_status_row(
        "OpenRouter",
        status.get("openrouter", False),
    )

    render_status_row(
        "Groq",
        status.get("groq", False),
    )

    render_status_row(
        "Cerebras",
        status.get("cerebras", False),
    )

    render_status_row(
        "Mistral",
        status.get("mistral", False),
    )

    render_status_row(
        "Anthropic",
        status.get("anthropic", False),
    )

    st.markdown(
        "<div style='height:4px'></div>",
        unsafe_allow_html=True,
    )

    render_status_row(
        "NVIDIA Image",
        status.get("nvidia", False),
    )

    render_status_row(
        "Hugging Face Image",
        status.get("huggingface", False),
    )

    render_status_row(
        "Tavily Search",
        status.get("tavily", False),
    )

    render_status_row(
        "PostgreSQL",
        status.get("database", False),
    )

    render_status_row(
        "Telegram",
        status.get("telegram", False),
    )


def render_status_row(
    name,
    connected,
):

    if connected:

        st.markdown(
            f"""
            <div style="
                display:flex;
                align-items:center;
                justify-content:space-between;
                padding:3px 0;
            ">
                <span>{name}</span>
                <span style="
                    font-size:11px;
                    opacity:0.75;
                ">
                    ● Connected
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            f"""
            <div style="
                display:flex;
                align-items:center;
                justify-content:space-between;
                padding:3px 0;
                opacity:0.55;
            ">
                <span>{name}</span>
                <span style="
                    font-size:11px;
                ">
                    ○ Offline
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# CURRENT CHAT
# ============================================================

def render_current_chat_section():

    st.markdown("**Current chat**")

    if st.button(
        "🧹  Clear conversation",
        use_container_width=True,
        key="sidebar_clear_chat",
    ):
        _clear_messages()

    uploaded_files = st.session_state.get(
        "uploaded_files",
        [],
    )

    if uploaded_files:

        st.caption(
            f"📎 {len(uploaded_files)} file(s) attached"
        )

        if st.button(
            "Remove attached files",
            use_container_width=True,
            key="sidebar_clear_files",
        ):
            st.session_state[
                "uploaded_files"
            ] = []

            st.session_state[
                "file_context"
            ] = ""

            st.rerun()

    else:

        st.caption(
            "No files attached"
        )


# ============================================================
# SETTINGS
# ============================================================

def render_settings_section():

    st.markdown("**Settings**")

    # --------------------------------------------------------
    # IMPORTANT:
    # Initialize session-state values BEFORE creating widgets.
    # Do NOT use value= together with a key that already exists.
    # --------------------------------------------------------

    if "show_provider_info" not in st.session_state:
        st.session_state[
            "show_provider_info"
        ] = True

    if "enable_chat_memory" not in st.session_state:
        st.session_state[
            "enable_chat_memory"
        ] = True

    if "confirm_image_generation" not in st.session_state:
        st.session_state[
            "confirm_image_generation"
        ] = True

    with st.expander(
        "⚙️  App settings",
        expanded=False,
    ):

        st.checkbox(
            "Show provider information",
            key="show_provider_info",
        )

        st.checkbox(
            "Enable chat memory",
            key="enable_chat_memory",
        )

        st.checkbox(
            "Confirm image generation",
            disabled=True,
            key="confirm_image_generation",
        )

        st.caption(
            "Image generation always requires "
            "your confirmation."
        )


# ============================================================
# FOOTER
# ============================================================

def render_footer():

    st.caption("My AI Agent")

    st.caption(
        "Streamlit • PostgreSQL • Multi-AI"
    )


# ============================================================
# RESET CHAT
# ============================================================

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

    st.session_state[
        "pending_image_prompt"
    ] = None

    st.session_state[
        "conversation_id"
    ] = None

    st.rerun()


# ============================================================
# CLEAR CURRENT CHAT
# ============================================================

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

    st.session_state[
        "pending_image_prompt"
    ] = None

    st.rerun()
