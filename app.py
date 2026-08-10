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
st.caption("Online AI Agent • Gemini + OpenRouter + Tavily")


# ============================================================
# API CLIENT
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

            response_data = response.read().decode(
                "utf-8"
            )

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
            f"Tavily HTTP {error.code}: "
            f"{error_body[:500]}"
        )

    except urllib.error.URLError as error:

        raise RuntimeError(
            f"Tavily connection error: {error.reason}"
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

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OPENROUTER_URL,
        data=data,
        headers={
            "Authorization": (
                f"Bearer {OPENROUTER_API_KEY}"
            ),
            "Content-Type": "application/json",
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

            response_data = response.read().decode(
                "utf-8"
            )

        result = json.loads(response_data)

        answer = (
            result["choices"][0]
            ["message"]["content"]
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

            with st.spinner("Web par search kar raha hoon..."):

                search_answer, search_results = (
                    search_web(user_input)
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
- If web search information is provided, use it for
  current/fresh information.
- Keep answers practical and easy to understand.

IMPORTANT:

You have access to conversation memory below.

CONVERSATION MEMORY:
{conversation}

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

                if web_context:
                    provider_text = (
                        f"{provider} + Tavily Web Search"
                    )
                else:
                    provider_text = provider

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

                st.caption(str(error))
