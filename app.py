import os
import json
import uuid
import urllib.request
import urllib.error

import streamlit as st
import psycopg


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="My AI Agent",
    page_icon="🤖",
    layout="centered",
)


# ============================================================
# CONFIG
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

GEMINI_MODEL = "gemini-2.5-flash"
OPENROUTER_MODEL = "openrouter/free"

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

TAVILY_URL = "https://api.tavily.com/search"

APP_NAME = "My AI Agent"


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "database_initialized" not in st.session_state:
    st.session_state.database_initialized = False

if "database_error" not in st.session_state:
    st.session_state.database_error = None

if "memory_loaded" not in st.session_state:
    st.session_state.memory_loaded = False

if "last_provider" not in st.session_state:
    st.session_state.last_provider = None


# ============================================================
# HEADER
# ============================================================

st.title("🤖 My AI Agent")

st.caption(
    "Online AI Agent • Gemini + OpenRouter + Tavily + PostgreSQL"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def database_available():
    return bool(DATABASE_URL)


def database_query(
    query,
    params=None,
    fetch="none",
):
    """
    Server-side PostgreSQL helper.

    The AI model never receives DATABASE_URL.
    The AI model never executes arbitrary SQL.
    """

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    with psycopg.connect(
        DATABASE_URL,
        connect_timeout=10,
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                query,
                params or (),
            )

            if fetch == "one":
                return cursor.fetchone()

            if fetch == "all":
                return cursor.fetchall()

            return None


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    if not database_available():
        return False

    statements = [

        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            external_id TEXT UNIQUE NOT NULL,
            display_name TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,

        """
        CREATE TABLE IF NOT EXISTS conversations (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL
                REFERENCES users(id)
                ON DELETE CASCADE,
            title TEXT NOT NULL DEFAULT 'New Conversation',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,

        """
        CREATE TABLE IF NOT EXISTS messages (
            id BIGSERIAL PRIMARY KEY,
            conversation_id BIGINT NOT NULL
                REFERENCES conversations(id)
                ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            provider TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,

        """
        CREATE TABLE IF NOT EXISTS agent_runs (
            id BIGSERIAL PRIMARY KEY,
            conversation_id BIGINT NOT NULL
                REFERENCES conversations(id)
                ON DELETE CASCADE,
            message_id BIGINT
                REFERENCES messages(id)
                ON DELETE SET NULL,
            provider TEXT,
            model TEXT,
            status TEXT NOT NULL,
            error_message TEXT,
            started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ,
            metadata JSONB
        );
        """,

        """
        CREATE TABLE IF NOT EXISTS user_settings (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL
                REFERENCES users(id)
                ON DELETE CASCADE,
            setting_key TEXT NOT NULL,
            setting_value TEXT,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(user_id, setting_key)
        );
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_conversations_user_id
        ON conversations(user_id);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
        ON messages(conversation_id);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_agent_runs_conversation_id
        ON agent_runs(conversation_id);
        """,

        """
        CREATE INDEX IF NOT EXISTS idx_user_settings_user_id
        ON user_settings(user_id);
        """,
    ]

    with psycopg.connect(
        DATABASE_URL,
        connect_timeout=10,
    ) as connection:

        with connection.cursor() as cursor:

            for statement in statements:
                cursor.execute(statement)

        connection.commit()

    return True


# ============================================================
# ENSURE DATABASE
# ============================================================

def ensure_database_initialized():

    if st.session_state.database_initialized:
        return

    if not database_available():

        st.session_state.database_error = (
            "DATABASE_URL is not configured."
        )

        return

    try:

        initialize_database()

        st.session_state.database_initialized = True
        st.session_state.database_error = None

    except Exception as error:

        st.session_state.database_error = str(error)


ensure_database_initialized()


# ============================================================
# USER
# ============================================================

def get_or_create_user():

    if not database_available():
        return None

    external_id = f"streamlit-{st.session_state.session_id}"

    row = database_query(
        """
        SELECT id
        FROM users
        WHERE external_id = %s
        LIMIT 1;
        """,
        (external_id,),
        fetch="one",
    )

    if row:
        return row[0]

    row = database_query(
        """
        INSERT INTO users (
            external_id,
            display_name
        )
        VALUES (%s, %s)
        RETURNING id;
        """,
        (
            external_id,
            "Anonymous User",
        ),
        fetch="one",
    )

    return row[0]


# ============================================================
# CONVERSATION
# ============================================================

def get_latest_conversation(user_id):

    if not user_id:
        return None

    row = database_query(
        """
        SELECT id
        FROM conversations
        WHERE user_id = %s
        ORDER BY updated_at DESC, id DESC
        LIMIT 1;
        """,
        (user_id,),
        fetch="one",
    )

    if row:
        return row[0]

    return None


def create_conversation(user_id):

    if not user_id:
        return None

    row = database_query(
        """
        INSERT INTO conversations (
            user_id,
            title
        )
        VALUES (%s, %s)
        RETURNING id;
        """,
        (
            user_id,
            "My AI Agent Conversation",
        ),
        fetch="one",
    )

    return row[0]


# ============================================================
# LOAD CONVERSATION
# ============================================================

def load_conversation_messages(
    conversation_id,
):

    if not conversation_id:
        return []

    rows = database_query(
        """
        SELECT
            role,
            content,
            provider
        FROM messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC, id ASC;
        """,
        (conversation_id,),
        fetch="all",
    )

    loaded_messages = []

    for row in rows:

        loaded_messages.append(
            {
                "role": row[0],
                "content": row[1],
                "provider": row[2],
            }
        )

    return loaded_messages


# ============================================================
# PERSISTENT MEMORY LOAD
# ============================================================

def load_persistent_memory():

    if st.session_state.memory_loaded:
        return

    if not st.session_state.database_initialized:
        return

    try:

        st.session_state.user_id = (
            get_or_create_user()
        )

        st.session_state.conversation_id = (
            get_latest_conversation(
                st.session_state.user_id
            )
        )

        if not st.session_state.conversation_id:

            st.session_state.conversation_id = (
                create_conversation(
                    st.session_state.user_id
                )
            )

        st.session_state.messages = (
            load_conversation_messages(
                st.session_state.conversation_id
            )
        )

        st.session_state.memory_loaded = True

    except Exception as error:

        st.session_state.database_error = str(error)


load_persistent_memory()


# ============================================================
# SAVE MESSAGE
# ============================================================

def save_message(
    conversation_id,
    role,
    content,
    provider=None,
):

    if not conversation_id:
        return None

    row = database_query(
        """
        INSERT INTO messages (
            conversation_id,
            role,
            content,
            provider
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id;
        """,
        (
            conversation_id,
            role,
            content,
            provider,
        ),
        fetch="one",
    )

    database_query(
        """
        UPDATE conversations
        SET updated_at = NOW()
        WHERE id = %s;
        """,
        (conversation_id,),
    )

    return row[0]


# ============================================================
# AGENT RUN TRACKING
# ============================================================

def start_agent_run(
    conversation_id,
    provider,
    model,
):

    if not conversation_id:
        return None

    row = database_query(
        """
        INSERT INTO agent_runs (
            conversation_id,
            provider,
            model,
            status,
            metadata
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (
            conversation_id,
            provider,
            model,
            "running",
            json.dumps(
                {
                    "application": APP_NAME,
                }
            ),
        ),
        fetch="one",
    )

    return row[0]


def finish_agent_run(
    run_id,
    status,
    message_id=None,
    error_message=None,
):

    if not run_id:
        return

    database_query(
        """
        UPDATE agent_runs
        SET
            status = %s,
            message_id = %s,
            error_message = %s,
            completed_at = NOW()
        WHERE id = %s;
        """,
        (
            status,
            message_id,
            error_message,
            run_id,
        ),
    )


# ============================================================
# DATABASE INFO
# ============================================================

def test_database_connection():

    row = database_query(
        "SELECT 1;",
        fetch="one",
    )

    if not row or row[0] != 1:

        raise RuntimeError(
            "PostgreSQL connection test failed."
        )

    return {
        "status": "connected",
        "database_test": "SELECT 1 successful",
    }


def get_database_info():

    row = database_query(
        """
        SELECT
            current_database(),
            current_user,
            version();
        """,
        fetch="one",
    )

    return {
        "status": "connected",
        "database": row[0],
        "user": row[1],
        "version": row[2],
    }


def list_database_tables():

    rows = database_query(
        """
        SELECT
            table_schema,
            table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN (
            'pg_catalog',
            'information_schema'
        )
        AND table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name;
        """,
        fetch="all",
    )

    return [
        {
            "schema": row[0],
            "table": row[1],
        }
        for row in rows
    ]


# ============================================================
# AGENT RUNS TOOL
# ============================================================

def get_latest_agent_runs(limit=10):

    safe_limit = max(
        1,
        min(int(limit), 25),
    )

    rows = database_query(
        f"""
        SELECT
            ar.id,
            ar.conversation_id,
            ar.message_id,
            ar.provider,
            ar.model,
            ar.status,
            ar.error_message,
            ar.started_at,
            ar.completed_at
        FROM agent_runs AS ar
        ORDER BY ar.started_at DESC, ar.id DESC
        LIMIT {safe_limit};
        """,
        fetch="all",
    )

    runs = []

    for row in rows:

        runs.append(
            {
                "id": row[0],
                "conversation_id": row[1],
                "message_id": row[2],
                "provider": row[3],
                "model": row[4],
                "status": row[5],
                "error_message": row[6],
                "started_at": (
                    row[7].isoformat()
                    if row[7]
                    else None
                ),
                "completed_at": (
                    row[8].isoformat()
                    if row[8]
                    else None
                ),
            }
        )

    return runs


# ============================================================
# CONVERSATION HISTORY TOOL
# ============================================================

def get_current_conversation_history(
    limit=50,
):

    conversation_id = (
        st.session_state.conversation_id
    )

    if not conversation_id:

        return {
            "conversation_id": None,
            "messages": [],
        }

    safe_limit = max(
        1,
        min(int(limit), 100),
    )

    rows = database_query(
        f"""
        SELECT
            id,
            role,
            content,
            provider,
            created_at
        FROM messages
        WHERE conversation_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT {safe_limit};
        """,
        (conversation_id,),
        fetch="all",
    )

    messages = []

    for row in reversed(rows):

        messages.append(
            {
                "id": row[0],
                "role": row[1],
                "content": row[2],
                "provider": row[3],
                "created_at": (
                    row[4].isoformat()
                    if row[4]
                    else None
                ),
            }
        )

    return {
        "conversation_id": conversation_id,
        "messages": messages,
    }


# ============================================================
# MEMORY SEARCH
# ============================================================

def search_memory(
    user_input,
    limit=20,
):

    if not st.session_state.conversation_id:

        return []

    query_text = user_input.strip()

    if not query_text:
        return []

    safe_limit = max(
        1,
        min(int(limit), 50),
    )

    # --------------------------------------------------------
    # First: exact/keyword-style search using PostgreSQL
    # --------------------------------------------------------

    rows = database_query(
        f"""
        SELECT
            id,
            role,
            content,
            provider,
            created_at
        FROM messages
        WHERE conversation_id = %s
          AND content ILIKE %s
        ORDER BY created_at DESC, id DESC
        LIMIT {safe_limit};
        """,
        (
            st.session_state.conversation_id,
            f"%{query_text}%",
        ),
        fetch="all",
    )

    if rows:

        results = []

        for row in reversed(rows):

            results.append(
                {
                    "id": row[0],
                    "role": row[1],
                    "content": row[2],
                    "provider": row[3],
                    "created_at": (
                        row[4].isoformat()
                        if row[4]
                        else None
                    ),
                }
            )

        return results

    # --------------------------------------------------------
    # Fallback: return recent memory for AI to interpret
    # --------------------------------------------------------

    recent_rows = database_query(
        f"""
        SELECT
            id,
            role,
            content,
            provider,
            created_at
        FROM messages
        WHERE conversation_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT {safe_limit};
        """,
        (
            st.session_state.conversation_id,
        ),
        fetch="all",
    )

    results = []

    for row in reversed(recent_rows):

        results.append(
            {
                "id": row[0],
                "role": row[1],
                "content": row[2],
                "provider": row[3],
                "created_at": (
                    row[4].isoformat()
                    if row[4]
                    else None
                ),
            }
        )

    return results


# ============================================================
# MEMORY INTENT DETECTION
# ============================================================

def detect_memory_intent(
    user_input,
):

    text = user_input.lower().strip()

    memory_phrases = [

        "what do you remember",
        "what did i tell you",
        "what did i tell u",
        "do you remember",
        "remember my",
        "my secret project",
        "secret project name",
        "favorite project",
        "my favorite project",
        "what is my project name",
        "what's my project name",
        "what is my secret",
        "what's my secret",
        "saved memory",
        "show my memory",
        "my saved memory",
        "previously told you",
        "from our previous conversation",
        "from previous conversation",
        "from our conversation",
        "previous conversation",
        "conversation memory",
        "memory",
    ]

    return any(
        phrase in text
        for phrase in memory_phrases
    )


# ============================================================
# DATABASE COMMAND DETECTION
# ============================================================

def detect_database_command(
    user_input,
):

    text = user_input.lower().strip()

    # --------------------------------------------------------
    # AGENT RUNS
    # --------------------------------------------------------

    if any(
        phrase in text
        for phrase in [
            "latest agent runs",
            "latest agent run",
            "recent agent runs",
            "recent agent run",
            "show agent runs",
            "show me agent runs",
            "agent run history",
            "agent runs",
            "agent run",
        ]
    ):

        return "latest_agent_runs"

    # --------------------------------------------------------
    # CONVERSATION HISTORY
    # --------------------------------------------------------

    if any(
        phrase in text
        for phrase in [
            "conversation history",
            "chat history",
            "show my history",
            "show conversation",
            "message history",
        ]
    ):

        return "conversation_history"

    # --------------------------------------------------------
    # SAVED MEMORY
    # --------------------------------------------------------

    if any(
        phrase in text
        for phrase in [
            "saved memory",
            "show my memory",
            "what do you remember",
            "what is in memory",
            "show memory",
        ]
    ):

        return "saved_memory"

    # --------------------------------------------------------
    # TABLES
    # --------------------------------------------------------

    if (
        "list database tables" in text
        or "list tables" in text
        or "show database tables" in text
        or "show tables" in text
    ):

        return "list_tables"

    # --------------------------------------------------------
    # DATABASE INFO
    # --------------------------------------------------------

    if (
        "database info" in text
        or "database information" in text
        or "postgres info" in text
        or "postgresql info" in text
    ):

        return "database_info"

    # --------------------------------------------------------
    # CONNECTION TEST
    # --------------------------------------------------------

    if (
        "test database connection" in text
        or "database connection" in text
        or "test database" in text
        or "postgres connection" in text
        or "postgresql connection" in text
        or "database health" in text
    ):

        return "test_connection"

    return None


# ============================================================
# RUN DATABASE TOOL
# ============================================================

def run_database_tool(
    user_input,
):

    command = detect_database_command(
        user_input
    )

    if not command:
        return None

    if not database_available():

        return {
            "tool": "PostgreSQL",
            "status": "not_configured",
            "message": (
                "DATABASE_URL is not configured."
            ),
        }

    try:

        if command == "test_connection":

            result = (
                test_database_connection()
            )

        elif command == "database_info":

            result = get_database_info()

        elif command == "list_tables":

            result = {
                "status": "connected",
                "tables": (
                    list_database_tables()
                ),
            }

        elif command == "latest_agent_runs":

            result = {
                "status": "success",
                "runs": (
                    get_latest_agent_runs(
                        limit=10
                    )
                ),
            }

        elif command == "conversation_history":

            result = {
                "status": "success",
                **get_current_conversation_history(
                    limit=50
                ),
            }

        elif command == "saved_memory":

            result = {
                "status": "success",
                **get_current_conversation_history(
                    limit=50
                ),
            }

        else:

            result = {
                "status": "error",
                "message": (
                    "Unknown PostgreSQL tool."
                ),
            }

        return {
            "tool": "PostgreSQL",
            **result,
        }

    except Exception as error:

        return {
            "tool": "PostgreSQL",
            "status": "error",
            "message": str(error),
        }


# ============================================================
# RUN MEMORY TOOL
# ============================================================

def run_memory_tool(
    user_input,
):

    if not detect_memory_intent(
        user_input
    ):

        return None

    if not database_available():

        return {
            "tool": "PostgreSQL Memory",
            "status": "not_configured",
            "memory": [],
        }

    try:

        results = search_memory(
            user_input,
            limit=30,
        )

        return {
            "tool": "PostgreSQL Memory",
            "status": "success",
            "memory": results,
        }

    except Exception as error:

        return {
            "tool": "PostgreSQL Memory",
            "status": "error",
            "message": str(error),
            "memory": [],
        }


# ============================================================
# TAVILY WEB SEARCH
# ============================================================

def search_web(
    query,
):

    if not TAVILY_API_KEY:

        raise RuntimeError(
            "TAVILY_API_KEY is not configured."
        )

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True,
        "max_results": 5,
    }

    data = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(
        TAVILY_URL,
        data=data,
        headers={
            "Content-Type": (
                "application/json"
            ),
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=60,
        ) as response:

            response_data = (
                response
                .read()
                .decode("utf-8")
            )

        result = json.loads(
            response_data
        )

        answer = result.get(
            "answer",
            "",
        )

        results = result.get(
            "results",
            [],
        )

        sources = []

        for item in results:

            sources.append(
                "TITLE: "
                + item.get("title", "")
                + "\nURL: "
                + item.get("url", "")
                + "\nCONTENT: "
                + item.get("content", "")
            )

        return (
            answer,
            "\n\n".join(sources),
        )

    except urllib.error.HTTPError as error:

        body = error.read().decode(
            "utf-8",
            errors="ignore",
        )

        raise RuntimeError(
            f"Tavily HTTP {error.code}: "
            f"{body[:500]}"
        )


# ============================================================
# GEMINI
# ============================================================

def ask_gemini(
    prompt,
):

    if not GEMINI_API_KEY:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt,
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096,
        },
    }

    data = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        data=data,
        headers={
            "Content-Type": (
                "application/json"
            ),
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=90,
        ) as response:

            response_data = (
                response
                .read()
                .decode("utf-8")
            )

        result = json.loads(
            response_data
        )

        candidates = result.get(
            "candidates",
            [],
        )

        if not candidates:

            raise RuntimeError(
                "Gemini returned no candidates."
            )

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        answer = "".join(
            part.get("text", "")
            for part in parts
        ).strip()

        if not answer:

            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return answer

    except urllib.error.HTTPError as error:

        body = error.read().decode(
            "utf-8",
            errors="ignore",
        )

        raise RuntimeError(
            f"Gemini HTTP {error.code}: "
            f"{body[:500]}"
        )


# ============================================================
# OPENROUTER
# ============================================================

def ask_openrouter(
    prompt,
):

    if not OPENROUTER_API_KEY:

        raise RuntimeError(
            "OPENROUTER_API_KEY is not configured."
        )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    data = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(
        OPENROUTER_URL,
        data=data,
        headers={
            "Authorization": (
                f"Bearer {OPENROUTER_API_KEY}"
            ),
            "Content-Type": (
                "application/json"
            ),
            "HTTP-Referer": (
                "https://my-ai-agent-8no8.onrender.com"
            ),
            "X-Title": APP_NAME,
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=90,
        ) as response:

            response_data = (
                response
                .read()
                .decode("utf-8")
            )

        result = json.loads(
            response_data
        )

        choices = result.get(
            "choices",
            [],
        )

        if not choices:

            raise RuntimeError(
                "OpenRouter returned no choices."
            )

        answer = (
            choices[0]
            .get("message", {})
            .get("content", "")
        )

        if not answer:

            raise RuntimeError(
                "OpenRouter returned empty response."
            )

        return answer

    except urllib.error.HTTPError as error:

        body = error.read().decode(
            "utf-8",
            errors="ignore",
        )

        raise RuntimeError(
            f"OpenRouter HTTP {error.code}: "
            f"{body[:500]}"
        )


# ============================================================
# AI ROUTER
# ============================================================

def ask_ai(
    prompt,
):

    gemini_error = None
    openrouter_error = None

    if GEMINI_API_KEY:

        try:

            answer = ask_gemini(
                prompt
            )

            return (
                answer,
                "Gemini",
                GEMINI_MODEL,
            )

        except Exception as error:

            gemini_error = str(error)

    if OPENROUTER_API_KEY:

        try:

            answer = ask_openrouter(
                prompt
            )

            return (
                answer,
                "OpenRouter",
                OPENROUTER_MODEL,
            )

        except Exception as error:

            openrouter_error = str(error)

    errors = []

    if gemini_error:

        errors.append(
            f"Gemini: {gemini_error}"
        )

    if openrouter_error:

        errors.append(
            f"OpenRouter: {openrouter_error}"
        )

    if not errors:

        raise RuntimeError(
            "No AI provider is configured."
        )

    raise RuntimeError(
        " | ".join(errors)
    )


# ============================================================
# BUILD MEMORY
# ============================================================

def build_memory():

    if not st.session_state.messages:

        return "No previous conversation."

    parts = []

    for message in (
        st.session_state.messages
    ):

        role = message[
            "role"
        ].upper()

        content = message[
            "content"
        ]

        parts.append(
            f"{role}: {content}"
        )

    return "\n\n".join(parts)


# ============================================================
# DATABASE STATUS
# ============================================================

if st.session_state.database_error:

    st.warning(
        "PostgreSQL issue: "
        + st.session_state.database_error
    )


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in (
    st.session_state.messages
):

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )

        if message["role"] == "assistant":

            provider = message.get(
                "provider"
            )

            if provider:

                st.caption(
                    f"Powered by {provider}"
                )


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Apne AI Agent ko command do..."
)


# ============================================================
# PROCESS USER MESSAGE
# ============================================================

if user_input:

    # --------------------------------------------------------
    # SAVE USER TO SESSION
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.chat_message("user"):

        st.markdown(
            user_input
        )

    # --------------------------------------------------------
    # SAVE USER TO DATABASE
    # --------------------------------------------------------

    try:

        save_message(
            conversation_id=(
                st.session_state.conversation_id
            ),
            role="user",
            content=user_input,
        )

    except Exception as error:

        st.session_state.database_error = str(
            error
        )

    # --------------------------------------------------------
    # BUILD NORMAL CONVERSATION MEMORY
    # --------------------------------------------------------

    conversation = build_memory()

    # --------------------------------------------------------
    # DATABASE COMMAND TOOL
    # --------------------------------------------------------

    database_result = (
        run_database_tool(
            user_input
        )
    )

    # --------------------------------------------------------
    # MEMORY SEARCH TOOL
    # --------------------------------------------------------

    memory_result = (
        run_memory_tool(
            user_input
        )
    )

    # --------------------------------------------------------
    # DATABASE CONTEXT
    # --------------------------------------------------------

    database_context = ""

    if database_result:

        database_context = (
            "POSTGRESQL DATABASE TOOL RESULT:\n"
            + json.dumps(
                database_result,
                indent=2,
                default=str,
            )
        )

    # --------------------------------------------------------
    # MEMORY CONTEXT
    # --------------------------------------------------------

    memory_context = ""

    if memory_result:

        memory_context = (
            "POSTGRESQL MEMORY TOOL RESULT:\n"
            + json.dumps(
                memory_result,
                indent=2,
                default=str,
            )
        )

    # --------------------------------------------------------
    # WEB SEARCH DETECTION
    # --------------------------------------------------------

    search_words = [
        "latest",
        "today",
        "news",
        "current",
        "recent",
        "abhi",
        "aaj",
        "latest update",
        "price",
        "weather",
        "search",
        "internet",
        "online",
        "who is",
        "what happened",
    ]

    should_search = any(
        word in user_input.lower()
        for word in search_words
    )

    # --------------------------------------------------------
    # DO NOT SEARCH WEB FOR DATABASE/MEMORY
    # --------------------------------------------------------

    if database_result:

        should_search = False

    if memory_result:

        should_search = False

    # --------------------------------------------------------
    # WEB CONTEXT
    # --------------------------------------------------------

    web_context = ""

    if (
        should_search
        and TAVILY_API_KEY
    ):

        try:

            with st.spinner(
                "Web par search kar raha hoon..."
            ):

                (
                    search_answer,
                    search_sources,
                ) = search_web(
                    user_input
                )

            web_context = (
                "WEB SEARCH ANSWER:\n"
                + search_answer
                + "\n\nWEB SOURCES:\n"
                + search_sources
            )

        except Exception as error:

            web_context = (
                "Web search failed: "
                + str(error)
            )

    # --------------------------------------------------------
    # AI PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are My AI Agent.

You have access to:
1. Conversation memory
2. PostgreSQL database tools
3. PostgreSQL persistent memory
4. Tavily web search context
5. Gemini / OpenRouter

IMPORTANT MEMORY RULES:

- If PostgreSQL Memory Tool Result contains
  information relevant to the user's question,
  answer using that actual memory.
- Do not say you cannot access memory if memory
  data is supplied below.
- Do not invent memories.
- If the exact answer is present in memory,
  give the answer directly.
- For questions like:
  "What is my secret project name?"
  "What is my favorite project?"
  "What do you remember about me?"
  use PostgreSQL memory when supplied.
- Do not use Tavily for personal memory.
- Personal memory has priority over web search.

IMPORTANT DATABASE RULES:

- Never invent database rows.
- Never invent table names.
- Never claim a database query ran unless the
  application supplied a PostgreSQL result.
- Never expose DATABASE_URL or secrets.
- PostgreSQL operations are performed server-side.

IMPORTANT WEB RULES:

- Current/latest information should use the supplied
  web search context when available.
- Do not use web information to answer personal memory
  questions.

CONVERSATION MEMORY:

{conversation}

POSTGRESQL DATABASE CONTEXT:

{database_context}

POSTGRESQL MEMORY CONTEXT:

{memory_context}

WEB SEARCH CONTEXT:

{web_context}

LATEST USER REQUEST:

{user_input}

Answer the user's latest request directly.
If the requested personal information is present
in PostgreSQL memory, answer from that memory.
"""

    # --------------------------------------------------------
    # AI RESPONSE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            run_id = None
            assistant_message_id = None

            try:

                (
                    answer,
                    provider,
                    model,
                ) = ask_ai(
                    prompt
                )

                # --------------------------------------------
                # START AGENT RUN
                # --------------------------------------------

                try:

                    run_id = start_agent_run(
                        conversation_id=(
                            st.session_state.conversation_id
                        ),
                        provider=provider,
                        model=model,
                    )

                except Exception as error:

                    st.session_state.database_error = (
                        str(error)
                    )

                # --------------------------------------------
                # PROVIDER LABEL
                # --------------------------------------------

                provider_parts = [
                    provider
                ]

                if web_context:

                    provider_parts.append(
                        "Tavily Web Search"
                    )

                if database_result:

                    provider_parts.append(
                        "PostgreSQL"
                    )

                if memory_result:

                    provider_parts.append(
                        "PostgreSQL Memory"
                    )

                provider_text = (
                    " + ".join(
                        provider_parts
                    )
                )

                # --------------------------------------------
                # DISPLAY
                # --------------------------------------------

                st.markdown(
                    answer
                )

                st.caption(
                    f"Powered by {provider_text}"
                )

                # --------------------------------------------
                # SESSION MEMORY
                # --------------------------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "provider": provider_text,
                    }
                )

                st.session_state.last_provider = (
                    provider_text
                )

                # --------------------------------------------
                # SAVE ASSISTANT MESSAGE
                # --------------------------------------------

                try:

                    assistant_message_id = (
                        save_message(
                            conversation_id=(
                                st.session_state.conversation_id
                            ),
                            role="assistant",
                            content=answer,
                            provider=provider_text,
                        )
                    )

                except Exception as error:

                    st.session_state.database_error = (
                        str(error)
                    )

                # --------------------------------------------
                # FINISH AGENT RUN
                # --------------------------------------------

                if run_id:

                    try:

                        finish_agent_run(
                            run_id=run_id,
                            status="success",
                            message_id=(
                                assistant_message_id
                            ),
                        )

                    except Exception as error:

                        st.session_state.database_error = (
                            str(error)
                        )

            except Exception as error:

                st.error(
                    "AI service temporarily unavailable."
                )

                st.caption(
                    str(error)
                )

                if run_id:

                    try:

                        finish_agent_run(
                            run_id=run_id,
                            status="failed",
                            error_message=str(
                                error
                            ),
                        )

                    except Exception:
                        pass
