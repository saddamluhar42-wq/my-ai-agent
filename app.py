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

GEMINI_MODEL = "gemini-2.5-flash"
OPENROUTER_MODEL = "openrouter/free"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


# ============================================================
# UI
# ============================================================

st.title("🤖 My AI Agent")
st.caption("Online AI Agent • Gemini + OpenRouter")


# ============================================================
# API CLIENTS
# ============================================================

gemini_client = None

if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
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


# ============================================================
# GEMINI FUNCTION
# ============================================================

def ask_gemini(prompt):
    if not gemini_client:
        raise RuntimeError("Gemini API key is not configured.")

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    answer = response.text

    if not answer:
        raise RuntimeError("Gemini returned an empty response.")

    return answer


# ============================================================
# OPENROUTER FUNCTION
# ============================================================

def ask_openrouter(prompt):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OpenRouter API key is not configured.")

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
        with urllib.request.urlopen(request, timeout=90) as response:
            response_data = response.read().decode("utf-8")

        result = json.loads(response_data)

        answer = result["choices"][0]["message"]["content"]

        if not answer:
            raise RuntimeError("OpenRouter returned an empty response.")

        return answer

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="ignore")

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
    # 1. TRY GEMINI FIRST
    # --------------------------------------------------------

    if GEMINI_API_KEY:
        try:
            answer = ask_gemini(prompt)
            return answer, "Gemini"
        except Exception as error:
            gemini_error = str(error)

    # --------------------------------------------------------
    # 2. FALLBACK TO OPENROUTER
    # --------------------------------------------------------

    if OPENROUTER_API_KEY:
        try:
            answer = ask_openrouter(prompt)
            return answer, "OpenRouter"
        except Exception as error:
            openrouter_error = str(error)

    # --------------------------------------------------------
    # 3. BOTH FAILED
    # --------------------------------------------------------

    errors = []

    if gemini_error:
        errors.append(f"Gemini: {gemini_error}")

    if openrouter_error:
        errors.append(f"OpenRouter: {openrouter_error}")

    if not errors:
        raise RuntimeError(
            "Neither GEMINI_API_KEY nor OPENROUTER_API_KEY is configured."
        )

    raise RuntimeError(" | ".join(errors))


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input("Apne AI Agent ko command do...")


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
        f'{message["role"].upper()}: {message["content"]}'
        for message in st.session_state.messages
    )

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

Conversation:

{conversation}

Respond to the latest user request.
"""

    # --------------------------------------------------------
    # GENERATE RESPONSE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:
                answer, provider = ask_ai(prompt)

                st.markdown(answer)

                # Small provider indicator
                st.caption(f"Powered by {provider}")

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            except Exception as error:

                st.error(
                    "AI service temporarily unavailable."
                )

                st.caption(str(error))
