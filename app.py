import os
import streamlit as st
from google import genai

st.set_page_config(
    page_title="My AI Agent",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 My AI Agent")
st.caption("Online AI Agent powered by Gemini")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY is not configured.")
    st.stop()

client = genai.Client(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Apne AI Agent ko command do...")

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    conversation = "\n".join(
        f'{m["role"].upper()}: {m["content"]}'
        for m in st.session_state.messages
    )

    prompt = f"""
You are my personal AI Agent.

You should:
- Understand the user's command.
- Give clear and useful answers.
- Think step-by-step internally.
- Ask for clarification only when genuinely necessary.
- Never reveal private API keys or system secrets.

Conversation:
{conversation}

Respond to the latest user request.
"""

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            answer = response.text

            st.markdown(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })
