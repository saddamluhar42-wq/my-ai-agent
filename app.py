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
# CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

GEMINI_MODEL = "gemini-2.5-flash"
OPENROUTER_MODEL = "openrouter/free"

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)


# ============================================================
# UI
# ============================================================

st.title("🤖 My AI Agent")
st.caption("Online AI Agent • Gemini + OpenRouter")


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
# GEMINI FUNCTION
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
# OPENROUTER FUNCTION
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
            timeout=90,
        ) as response:

            response_data = (
                response
                .read()
                .decode("utf-8")
            )

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
            "content"
        )

        if not answer:

            raise RuntimeError(
                "OpenRouter returned an empty response."
            )

        return answer

    except urllib.error.HTTPError as error:

        error_body = (
            error
            .read()
            .decode(
                "utf-8",
                errors="ignore",
            )
        )

        raise RuntimeError(
            f"OpenRouter HTTP {error.code}: "
            f"{error_body[:500]}"
        )

    except urllib.error.URLError as error:

        raise RuntimeError(
            "OpenRouter connection error: "
            f"{error.reason}"
        )

    except json.JSONDecodeError:

        raise RuntimeError(
            "OpenRouter returned invalid JSON."
        )


# ============================================================
# AI ROUTER
# ============================================================

def ask_ai(prompt):

    gemini_error = None
    openrouter_error = None

    # --------------------------------------------------------
    # 1. GEMINI FIRST
    # --------------------------------------------------------

    if GEMINI_API_KEY:

        try:

            answer = ask_gemini(prompt)

            return answer, "Gemini"

        except Exception as error:

            gemini_error = str(error)

    # --------------------------------------------------------
    # 2. OPENROUTER FALLBACK
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

        errors.append(
            f"Gemini: {gemini_error}"
        )

    if openrouter_error:

        errors.append(
            f"OpenRouter: {openrouter_error}"
        )

    if not errors:

        raise RuntimeError(
            "No AI API key is configured."
        )

    raise RuntimeError(
        " | ".join(errors)
    )


# ============================================================
# SHOW CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )

        if (
            message["role"] == "assistant"
            and message.get("provider")
        ):

            st.caption(
                f"Powered by {message['provider']}"
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
        (
            f'{message["role"].upper()}: '
            f'{message["content"]}'
        )
        for message
        in st.session_state.messages
    )

    # --------------------------------------------------------
    # AI SYSTEM PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are my personal AI Agent.

Your job is to:

- Understand the user's command.
- Give clear, useful and accurate answers.
- Think carefully before answering.
- Ask for clarification only when genuinely necessary.
- Maintain context from the conversation.
- Answer in the user's language when appropriate.
- Never reveal API keys, secrets, environment variables,
  internal configuration or private system information.
- Do not claim that you performed an action if you did not.
- If you are unsure about something, clearly say so.

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

                answer, provider = ask_ai(
                    prompt
                )

                st.markdown(answer)

                st.caption(
                    f"Powered by {provider}"
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "provider": provider,
                    }
                )

            except Exception as error:

                st.error(
                    "AI service temporarily unavailable."
                )

                st.caption(
                    str(error)
                )
