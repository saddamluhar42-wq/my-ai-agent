import os
import json
import urllib.request
import urllib.error

import streamlit as st
from google import genai


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

GEMINI_MODEL = "gemini-2.5-flash"
OPENROUTER_MODEL = "openrouter/free"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TAVILY_URL = "https://api.tavily.com/search"


# ============================================================
# UI
# ============================================================

st.title("🤖 My AI Agent")
st.caption("Online AI Agent • Gemini + OpenRouter + Web Search")


# ============================================================
# GEMINI CLIENT
# ============================================================

gemini_client = None

if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(
            api_key=GEMINI_API_KEY
        )
    except Exception:
        gemini_client = None


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# SHOW CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("provider"):
            st.caption(
                f"Powered by {message['provider']}"
            )


# ============================================================
# WEB SEARCH DETECTOR
# ============================================================

def needs_web_search(text):

    text = text.lower().strip()

    search_words = [
        "latest",
        "today",
        "current",
        "now",
        "news",
        "recent",
        "update",
        "updates",
        "2026",
        "price",
        "prices",
        "weather",
        "live",
        "trending",
        "new",
        "recently",
        "aaj",
        "abhi",
        "latest news",
        "current news",
        "taza khabar",
        "taaza khabar",
        "aaj ka",
        "abhi ka",
        "latest update",
    ]

    return any(
        word in text
        for word in search_words
    )


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
        "search_depth": "basic",
        "topic": "general",
        "max_results": 5,
        "include_answer": True,
        "include_raw_content": False,
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
            timeout=30
        ) as response:

            response_data = (
                response
                .read()
                .decode("utf-8")
            )

        result = json.loads(response_data)

        answer = result.get(
            "answer",
            ""
        )

        results = result.get(
            "results",
            []
        )

        search_context = []

        if answer:
            search_context.append(
                f"SEARCH SUMMARY:\n{answer}"
            )

        for item in results:

            title = item.get(
                "title",
                ""
            )

            content = item.get(
                "content",
                ""
            )

            url = item.get(
                "url",
                ""
            )

            search_context.append(
                f"TITLE: {title}\n"
                f"CONTENT: {content}\n"
                f"SOURCE: {url}"
            )

        if not search_context:

            raise RuntimeError(
                "Tavily returned no search results."
            )

        return "\n\n".join(
            search_context
        )

    except urllib.error.HTTPError as error:

        error_body = (
            error.read()
            .decode(
                "utf-8",
                errors="ignore"
            )
        )

        raise RuntimeError(
            f"Tavily HTTP {error.code}: "
            f"{error_body[:500]}"
        )

    except urllib.error.URLError as error:

        raise RuntimeError(
            f"Tavily connection error: "
            f"{error.reason}"
        )


# ============================================================
# GEMINI
# ============================================================

def ask_gemini(prompt):

    if not gemini_client:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    answer = response.text

    if not answer:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return answer


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
            "X-Title": "My AI Agent",
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=90
        ) as response:

            response_data = (
                response
                .read()
                .decode("utf-8")
            )

        result = json.loads(
            response_data
        )

        answer = (
            result["choices"][0]
            ["message"]["content"]
        )

        if not answer:
            raise RuntimeError(
                "OpenRouter returned "
                "an empty response."
            )

        return answer

    except urllib.error.HTTPError as error:

        error_body = (
            error.read()
            .decode(
                "utf-8",
                errors="ignore"
            )
        )

        raise RuntimeError(
            f"OpenRouter HTTP {error.code}: "
            f"{error_body[:500]}"
        )

    except urllib.error.URLError as error:

        raise RuntimeError(
            f"OpenRouter connection error: "
            f"{error.reason}"
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
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Apne AI Agent ko command do..."
)


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
    # BUILD CONVERSATION
    # --------------------------------------------------------

    conversation = "\n".join(
        f'{message["role"].upper()}: '
        f'{message["content"]}'
        for message
        in st.session_state.messages
    )

    # --------------------------------------------------------
    # WEB SEARCH
    # --------------------------------------------------------

    search_context = ""
    search_used = False

    if needs_web_search(user_input):

        try:

            with st.spinner(
                "Web par search kar raha hoon..."
            ):

                search_context = search_web(
                    user_input
                )

            search_used = True

        except Exception as error:

            st.warning(
                "Web search unavailable. "
                "AI se normal answer liya ja raha hai."
            )

    # --------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are my personal AI Agent.

Your job is to:

- Understand the user's command.
- Give clear and useful answers.
- Think carefully before answering.
- Ask for clarification only when genuinely necessary.
- Never reveal private API keys or system secrets.
- Maintain context from the conversation.
- Answer in the user's language when appropriate.
- Do not invent facts.
- If web search information is provided, use it for
  current information and prefer the provided sources.

Conversation:

{conversation}

Web Search Results:

{search_context}

Respond to the latest user request.
"""

    # --------------------------------------------------------
    # GENERATE RESPONSE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "Thinking..."
        ):

            try:

                answer, provider = ask_ai(
                    prompt
                )

                st.markdown(answer)

                if search_used:

                    st.caption(
                        f"Powered by {provider} + Tavily Web Search"
                    )

                else:

                    st.caption(
                        f"Powered by {provider}"
                    )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "provider": (
                            f"{provider} + Tavily"
                            if search_used
                            else provider
                        ),
                    }
                )

            except Exception as error:

                st.error(
                    "AI service temporarily unavailable."
                )

                st.caption(
                    str(error)
                )
