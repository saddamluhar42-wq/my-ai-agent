import streamlit as st

from config import (
    APP_NAME,
    APP_VERSION,
    get_config_status,
)

from database.connection import execute
from database.memory import load_conversation


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
# RECENT CONVERSATIONS
# ============================================================

def render_conversation_section():

    st.markdown("**Recent chats**")

    search_query = st.session_state.get(
        "chat_search_query",
        "",
    ).strip()

    conversations = _load_recent_conversations(
        search_query=search_query,
        limit=30,
    )

    if not conversations:

        if search_query:
            st.caption(
                "No matching conversations."
            )
        else:
            st.caption(
                "No conversations yet."
            )

        return

    current_conversation_id = (
        st.session_state.get(
            "conversation_id"
        )
    )

    for conversation in conversations:

        conversation_id = conversation[
            "id"
        ]

        title = conversation[
            "title"
        ]

        message_count = conversation[
            "message_count"
        ]

        source = conversation[
            "source"
        ]

        display_title = _clean_title(
            title
        )

        if len(display_title) > 30:
            display_title = (
                display_title[:30].rstrip()
                + "..."
            )

        if conversation_id == current_conversation_id:
            prefix = "●"
        else:
            prefix = "○"

        if source == "telegram":
            icon = "✈️"
        else:
            icon = "💬"

        label = (
            f"{prefix} {icon}  "
            f"{display_title}"
        )

        if message_count:
            label += (
                f"  ·  {message_count}"
            )

        if st.button(
            label,
            use_container_width=True,
            key=(
                "conversation_"
                f"{conversation_id}"
            ),
        ):
            _open_conversation(
                conversation_id
            )


# ============================================================
# DATABASE CHAT LOADER
# ============================================================

def _load_recent_conversations(
    search_query="",
    limit=30,
):

    safe_limit = max(
        1,
        min(int(limit), 100),
    )

    search_query = (
        search_query.strip()
        if search_query
        else ""
    )

    try:

        if search_query:

            rows = execute(
                f"""
                SELECT
                    c.id,
                    c.title,
                    c.created_at,
                    c.updated_at,

                    (
                        SELECT COUNT(*)
                        FROM messages m
                        WHERE m.conversation_id = c.id
                    ) AS message_count,

                    u.external_id,

                    COALESCE(
                        (
                            SELECT m2.content
                            FROM messages m2
                            WHERE
                                m2.conversation_id = c.id
                                AND m2.role = 'user'
                            ORDER BY
                                m2.created_at ASC,
                                m2.id ASC
                            LIMIT 1
                        ),
                        c.title
                    ) AS first_message

                FROM conversations c

                INNER JOIN users u
                    ON u.id = c.user_id

                WHERE
                    c.title ILIKE %s

                    OR EXISTS (
                        SELECT 1
                        FROM messages ms
                        WHERE
                            ms.conversation_id = c.id
                            AND ms.content ILIKE %s
                    )

                ORDER BY
                    c.updated_at DESC,
                    c.id DESC

                LIMIT {safe_limit};
                """,
                (
                    f"%{search_query}%",
                    f"%{search_query}%",
                ),
                fetch="all",
            )

        else:

            rows = execute(
                f"""
                SELECT
                    c.id,
                    c.title,
                    c.created_at,
                    c.updated_at,

                    (
                        SELECT COUNT(*)
                        FROM messages m
                        WHERE m.conversation_id = c.id
                    ) AS message_count,

                    u.external_id,

                    COALESCE(
                        (
                            SELECT m2.content
                            FROM messages m2
                            WHERE
                                m2.conversation_id = c.id
                                AND m2.role = 'user'
                            ORDER BY
                                m2.created_at ASC,
                                m2.id ASC
                            LIMIT 1
                        ),
                        c.title
                    ) AS first_message

                FROM conversations c

                INNER JOIN users u
                    ON u.id = c.user_id

                ORDER BY
                    c.updated_at DESC,
                    c.id DESC

                LIMIT {safe_limit};
                """,
                fetch="all",
            )

    except Exception as error:

        st.caption(
            "Unable to load chat history."
        )

        if st.session_state.get(
            "show_provider_info",
            True,
        ):
            st.caption(
                f"Database: {str(error)[:160]}"
            )

        return []

    conversations = []

    for row in rows:

        external_id = row[5] or ""

        if external_id.startswith(
            "telegram:"
        ):
            source = "telegram"
        else:
            source = "web"

        first_message = (
            row[6]
            or row[1]
            or "New Conversation"
        )

        title = (
            row[1]
            or first_message
            or "New Conversation"
        )

        conversations.append(
            {
                "id": row[0],
                "title": title,
                "created_at": row[2],
                "updated_at": row[3],
                "message_count": row[4] or 0,
                "external_id": external_id,
                "first_message": first_message,
                "source": source,
            }
        )

    return conversations


# ============================================================
# OPEN CONVERSATION
# ============================================================

def _open_conversation(
    conversation_id,
):

    try:

        messages = load_conversation(
            conversation_id,
            limit=100,
        )

        st.session_state[
            "conversation_id"
        ] = conversation_id

        st.session_state[
            "messages"
        ] = messages

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

    except Exception as error:

        st.error(
            "Could not open conversation: "
            + str(error)
        )


# ============================================================
# TITLE CLEANER
# ============================================================

def _clean_title(
    title,
):

    title = str(
        title or ""
    ).strip()

    if not title:
        return "New Conversation"

    return title


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

    current_provider = (
        st.session_state.get(
            "preferred_provider",
            "Auto",
        )
    )

    if current_provider not in provider_options:

        st.session_state[
            "preferred_provider"
        ] = "Auto"

        current_provider = "Auto"

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

    st.caption(
        "My AI Agent"
    )

    st.caption(
        "Streamlit • PostgreSQL • Multi-AI"
    )


# ============================================================
# NEW CHAT
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
