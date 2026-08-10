import os
import json
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

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TAVILY_URL = "https://api.tavily.com/search"


# ============================================================
# UI
# ============================================================

st.title("🤖 My AI Agent")
st.caption("Online AI Agent • Gemini + OpenRouter + Tavily + PostgreSQL")


# ============================================================
# SESSION MEMORY
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_provider" not in st.session_state:
    st.session_state.last_provider = None


# ============================================================
# SHOW CHAT HISTORY
# ============================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            provider = message.get("provider")

            if provider:
                st.caption(f"Powered by {provider}")


# ============================================================
# POSTGRESQL DATABASE
# ============================================================

def database_available():
    return bool(DATABASE_URL)


def database_query(query, params=None, fetch="all"):
    """
    Controlled PostgreSQL helper.

    AI ko arbitrary SQL execute karne ki permission nahi hai.
    Sirf application ke internally defined safe queries use hoti hain.
    """

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured.")

    with psycopg.connect(
        DATABASE_URL,
        connect_timeout=10
    ) as connection:

        with connection.cursor() as cursor:
            cursor.execute(query, params or ())

            if fetch == "one":
                return cursor.fetchone()

            if fetch == "all":
                return cursor.fetchall()

            return None


def test_database_connection():
    row = database_query(
        "SELECT 1;",
        fetch="one"
    )

    if not row or row[0] != 1:
        raise RuntimeError(
            "PostgreSQL connection test returned an unexpected result."
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
            version()
        """,
        fetch="one",
    )

    return {
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
        ORDER BY table_schema, table_name
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


def detect_database_command(user_input):
    """
    Common database requests detect karta hai.
    """

    text = user_input.lower().strip()

    database_words = [
        "database",
        "postgres",
        "postgresql",
        "db connection",
        "db connect",
        "db test",
        "database connection",
        "database test",
        "sql connection",
    ]

    if not any(word in text for word in database_words):
        return None

    if any(
        phrase in text
        for phrase in [
            "connection",
            "connect",
            "test",
            "health",
            "working",
            "status",
        ]
    ):
        return "test_connection"

    if any(
        phrase in text
        for phrase in [
            "table",
            "tables",
            "schema",
            "schemas",
        ]
    ):
        return "list_tables"

    if any(
        phrase in text
        for phrase in [
            "info",
            "information",
            "version",
            "details",
        ]
    ):
        return "database_info"

    return "test_connection"


def run_database_tool(user_input):
    command = detect_database_command(user_input)

    if not command:
        return None

    if not database_available():
        return {
            "tool": "PostgreSQL",
            "status": "not_configured",
            "message": "DATABASE_URL is not configured in the environment.",
        }

    try:

        if command == "test_connection":

            result = test_database_connection()

        elif command == "list_tables":

            result = {
                "status": "connected",
                "tables": list_database_tables(),
            }

        elif command == "database_info":

            result = {
                "status": "connected",
                **get_database_info(),
            }

        else:

            result = {
                "status": "error",
                "message": "Unknown database tool command.",
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
# TAVILY WEB SEARCH
# ============================================================

def search_web(query):

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

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        TAVILY_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            response_data = response.read().decode("utf-8")

        result = json.loads(response_data)

        answer = result.get("answer", "")
        results = result.get("results", [])

        sources = []

        for item in results:

            title = item.get("title", "")
            content = item.get("content", "")
            url = item.get("url", "")

            sources.append(
                f"TITLE: {title}\n"
                f"URL: {url}\n"
                f"CONTENT: {content}"
            )

        web_context = "\n\n".join(sources)

        return answer, web_context

    except urllib.error.HTTPError as error:

        error_body = error.read().decode(
            "utf-8",
            errors="ignore"
        )

        raise RuntimeError(
            f"Tavily HTTP {error.code}: {error_body[:500]}"
        )

    except urllib.error.URLError as error:

        raise RuntimeError(
            f"Tavily connection error: {error.reason}"
        )


# ============================================================
# GEMINI REST API
# ============================================================

def ask_gemini(prompt):

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096,
        },
    }

    data = json.dumps(payload).encode("utf-8")

    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=90
        ) as response:

            response_data = response.read().decode("utf-8")

        result = json.loads(response_data)

        candidates = result.get("candidates", [])

        if not candidates:
            raise RuntimeError(
                "Gemini returned no candidates."
            )

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        answer_parts = []

        for part in parts:

            text = part.get("text")

            if text:
                answer_parts.append(text)

        answer = "".join(answer_parts).strip()

        if not answer:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return answer

    except urllib.error.HTTPError as error:

        error_body = error.read().decode(
            "utf-8",
            errors="ignore"
        )

        raise RuntimeError(
            f"Gemini HTTP {error.code}: {error_body[:500]}"
        )

    except urllib.error.URLError as error:

        raise RuntimeError(
            f"Gemini connection error: {error.reason}"
        )


# ============================================================
# OPENROUTER
# ============================================================

def ask_openrouter(prompt):

    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OpenRouter API key is not configured."
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

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OPENROUTER_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://my-ai-agent-8no8.onrender.com",
            "X-Title": "My AI Agent",
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=90
        ) as response:

            response_data = response.read().decode("utf-8")

        result = json.loads(response_data)

        choices = result.get("choices", [])

        if not choices:
            raise RuntimeError(
                "OpenRouter returned no choices."
            )

        message = choices[0].get(
            "message",
            {}
        )

        answer = message.get(
            "content",
            ""
        )

        if not answer:
            raise RuntimeError(
                "OpenRouter returned an empty response."
            )

        return answer

    except urllib.error.HTTPError as error:

        error_body = error.read().decode(
            "utf-8",
            errors="ignore"
        )

        raise RuntimeError(
            f"OpenRouter HTTP {error.code}: {error_body[:500]}"
        )

    except urllib.error.URLError as error:

        raise RuntimeError(
            f"OpenRouter connection error: {error.reason}"
        )


# ============================================================
# AI ROUTER
# ============================================================

def ask_ai(prompt):

    gemini_error = None
    openrouter_error = None

    # --------------------------------------------------------
    # GEMINI FIRST
    # --------------------------------------------------------

    if GEMINI_API_KEY:

        try:

            answer = ask_gemini(prompt)

            return answer, "Gemini"

        except Exception as error:

            gemini_error = str(error)

    # --------------------------------------------------------
    # OPENROUTER FALLBACK
    # --------------------------------------------------------

    if OPENROUTER_API_KEY:

        try:

            answer = ask_openrouter(prompt)

            return answer, "OpenRouter"

        except Exception as error:

            openrouter_error = str(error)

    # --------------------------------------------------------
    # BOTH FAILED
    # --------------------------------------------------------

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
            "Neither GEMINI_API_KEY nor "
            "OPENROUTER_API_KEY is configured."
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

    memory_parts = []

    for message in st.session_state.messages:

        role = message["role"].upper()
        content = message["content"]

        memory_parts.append(
            f"{role}: {content}"
        )

    return "\n\n".join(memory_parts)


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
    # SAVE USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    # --------------------------------------------------------
    # BUILD MEMORY
    # --------------------------------------------------------

    conversation = build_memory()

    # --------------------------------------------------------
    # DATABASE TOOL
    # --------------------------------------------------------

    database_context = ""

    database_result = run_database_tool(
        user_input
    )

    if database_result is not None:

        database_context = (
            "POSTGRESQL DATABASE TOOL RESULT:\n"
            + json.dumps(
                database_result,
                indent=2,
                default=str
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

    web_context = ""

    # --------------------------------------------------------
    # OPTIONAL WEB SEARCH
    # --------------------------------------------------------

    if should_search and TAVILY_API_KEY:

        try:

            with st.spinner(
                "Web par search kar raha hoon..."
            ):

                search_answer, search_results = search_web(
                    user_input
                )

            web_context = (
                f"WEB SEARCH ANSWER:\n"
                f"{search_answer}\n\n"
                f"WEB SOURCES:\n"
                f"{search_results}"
            )

        except Exception as error:

            web_context = (
                "Web search failed. "
                "Answer using available knowledge."
            )

    # --------------------------------------------------------
    # AI PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are my personal AI Agent.

Your job is to:

- Understand the user's command.
- Give clear and useful answers.
- Think carefully before answering.
- Ask for clarification only when genuinely necessary.
- Never reveal API keys, passwords, tokens, or system secrets.
- Maintain conversation context.
- Answer in the user's language when appropriate.
- Do not invent current information.
- If web search information is provided, use it for current/fresh information.
- If PostgreSQL database tool information is provided, use the actual tool result.
- Never claim that you personally executed a database operation unless a PostgreSQL
  tool result is provided below.
- Keep answers practical and easy to understand.

DATABASE TOOL RULES:

- PostgreSQL is connected through the server-side DATABASE_URL environment variable.
- Database operations are performed by the application, not by Gemini directly.
- Do not invent database results.
- Do not invent tables, rows, versions, or connection status.
- If the database tool result says connected, clearly report that.
- If the database tool result says error, clearly report the error without exposing secrets.
- Never request or reveal the DATABASE_URL itself.

IMPORTANT:

You have access to conversation memory below.

CONVERSATION MEMORY:
{conversation}

POSTGRESQL DATABASE CONTEXT:
{database_context}

WEB SEARCH CONTEXT:
{web_context}

LATEST USER REQUEST:
{user_input}

Respond directly to the latest user request.
"""

    # --------------------------------------------------------
    # GENERATE RESPONSE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                answer, provider = ask_ai(prompt)

                st.markdown(answer)

                provider_parts = [
                    provider
                ]

                if web_context:
                    provider_parts.append(
                        "Tavily Web Search"
                    )

                if database_result is not None:
                    provider_parts.append(
                        "PostgreSQL"
                    )

                provider_text = " + ".join(
                    provider_parts
                )

                st.caption(
                    f"Powered by {provider_text}"
                )

                # ------------------------------------------------
                # SAVE ASSISTANT RESPONSE
                # ------------------------------------------------

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

            except Exception as error:

                st.error(
                    "AI service temporarily unavailable."
                )

                st.caption(
                    str(error)
                )
