from __future__ import annotations

import hashlib
import io
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from agent.core import run_agent
from agent.task_scheduler import DEFAULT_TIMEZONE
from ai.agent import AgentError, generate_image
from config import (
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL, DEEPSEEK_API_KEY, DEEPSEEK_MODEL,
    GEMINI_API_KEY, GEMINI_MODEL, KIMI_API_KEY, KIMI_MODEL,
    OPENAI_API_KEY, OPENAI_MODEL, OPENROUTER_API_KEY, OPENROUTER_MODEL,
    XAI_API_KEY, XAI_MODEL, YOU_API_KEY, YOU_MODEL,
    HF_TOKEN, HF_TOKEN_2, HF_TOKEN_3, HF_IMAGE_MODEL, TELEGRAM_BOT_TOKEN,
    DATABASE_URL,
)
from database.chat_history import list_recent_chats, load_chat, save_chat
from database.tasks import list_tasks
from ui.experience import apply as apply_ui, render_empty_state, render_header as render_optimized_header, thinking_status, finish_status, fail_status

APP_NAME = "My AI Agent"
APP_VERSION = "1.8.0"
MAX_FILE_SIZE_MB = 20
MAX_FILE_CONTEXT_CHARS = 18000

TIME_LOCATIONS = {
    "India — IST": ("Asia/Kolkata", "India"),
    "Ahmedabad, India — IST": ("Asia/Kolkata", "Ahmedabad, India"),
    "Mumbai, India — IST": ("Asia/Kolkata", "Mumbai, India"),
    "Delhi, India — IST": ("Asia/Kolkata", "Delhi, India"),
    "Dubai, UAE — GST": ("Asia/Dubai", "Dubai, UAE"),
    "London, UK": ("Europe/London", "London, UK"),
    "New York, USA": ("America/New_York", "New York, USA"),
    "Los Angeles, USA": ("America/Los_Angeles", "Los Angeles, USA"),
    "Tokyo, Japan": ("Asia/Tokyo", "Tokyo, Japan"),
    "Singapore": ("Asia/Singapore", "Singapore"),
}

st.set_page_config(page_title=APP_NAME, page_icon="🤖", layout="wide", initial_sidebar_state="expanded")
apply_ui()


def initialize_state() -> None:
    defaults = {
        "messages": [], "recent_context": [], "preferred_provider": "Auto", "file_context": "",
        "uploaded_names": [], "uploaded_signature": "", "pending_time_prompt": None, "pending_time_location": None,
        "last_time_location": "India — IST", "session_key": str(uuid.uuid4()),
        "browser_identity": str(uuid.uuid4()), "web_user_id": None,
        "chat_title": "New Chat", "history_loaded": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clean_text(value: object) -> str:
    return str(value or "").strip()


def get_web_user_id():
    if st.session_state.get("web_user_id") is not None:
        return st.session_state["web_user_id"]
    if not DATABASE_URL:
        return None
    try:
        from database.models import get_or_create_user
        user_id = get_or_create_user(
            external_id=f"web:{st.session_state['browser_identity']}",
            display_name="Web User",
        )
        st.session_state["web_user_id"] = int(user_id)
        return int(user_id)
    except Exception:
        return None


def owner_key() -> str:
    user_id = get_web_user_id()
    return f"user:{user_id}" if user_id is not None else f"browser:{st.session_state['browser_identity']}"


def safe_read_file(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()
    if len(raw) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File exceeds {MAX_FILE_SIZE_MB} MB limit.")
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(raw)).pages)
    if name.endswith(".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(io.BytesIO(raw)).paragraphs)
    return raw.decode("utf-8", errors="replace")


def process_files(files) -> None:
    if not files:
        return
    signature_source = "|".join(f"{f.name}:{getattr(f, 'size', 0)}" for f in files)
    signature = hashlib.sha256(signature_source.encode("utf-8")).hexdigest()
    if signature == st.session_state.get("uploaded_signature"):
        return
    chunks, names = [], []
    for uploaded in files:
        try:
            names.append(uploaded.name)
            text = safe_read_file(uploaded)
            chunks.append(f"FILE: {uploaded.name}\n{text[:MAX_FILE_CONTEXT_CHARS]}")
        except Exception as exc:
            st.error(f"{uploaded.name}: {exc}")
    st.session_state["uploaded_signature"] = signature
    if chunks:
        st.session_state["file_context"] = "\n\n---\n\n".join(chunks)
        st.session_state["uploaded_names"] = names


def is_time_query(prompt: str) -> bool:
    text = prompt.lower()
    phrases = (
        "time kya", "time bata", "kitne baje", "kitna time", "abhi time",
        "current time", "local time", "what time", "tell me the time", "time now",
        "samay kya", "samay bata", "waqt kya", "waqt bata", "clock time", "abhi kitne baje",
    )
    return any(phrase in text for phrase in phrases) or (
        "time" in text and any(word in text for word in ("abhi", "current", "local", "now"))
    )


def append_message(role: str, content: str, **extra) -> None:
    item = {"role": role, "content": content}
    item.update(extra)
    st.session_state["messages"].append(item)
    persist_current_chat()


def _history_title(messages) -> str:
    for message in messages:
        if message.get("role") == "user" and clean_text(message.get("content")):
            title = clean_text(message["content"]).replace("\n", " ")
            return title[:80] + ("..." if len(title) > 80 else "")
    return "New Chat"


def persist_current_chat() -> None:
    if not DATABASE_URL:
        return
    messages = []
    for message in st.session_state.get("messages", []):
        item = {"role": message.get("role", "assistant"), "content": clean_text(message.get("content"))}
        if message.get("provider"):
            item["provider"] = message["provider"]
        if message.get("model"):
            item["model"] = message["model"]
        if message.get("type") == "image":
            item["type"] = "image"
            item["content"] = item["content"] or "[Generated image]"
        messages.append(item)
    if not messages:
        return
    title = _history_title(messages)
    st.session_state["chat_title"] = title
    try:
        save_chat(st.session_state["session_key"], title, messages, owner_id=owner_key())
    except Exception:
        pass


def start_new_chat() -> None:
    persist_current_chat()
    st.session_state["messages"] = []
    st.session_state["recent_context"] = []
    st.session_state["file_context"] = ""
    st.session_state["uploaded_names"] = []
    st.session_state["uploaded_signature"] = ""
    st.session_state["pending_time_prompt"] = None
    st.session_state["pending_time_location"] = None
    st.session_state["session_key"] = str(uuid.uuid4())
    st.session_state["chat_title"] = "New Chat"
    st.rerun()


def open_history_chat(session_key: str) -> None:
    try:
        chat = load_chat(session_key, owner_id=owner_key())
    except Exception as exc:
        st.error(f"History load failed: {exc}")
        return
    if not chat:
        st.error("Chat not found or access denied.")
        return
    st.session_state["session_key"] = chat["session_key"]
    st.session_state["chat_title"] = chat["title"]
    st.session_state["messages"] = chat["messages"]
    st.session_state["recent_context"] = [
        {"role": m.get("role"), "content": m.get("content", "")} for m in chat["messages"][-20:]
    ]
    st.rerun()


def model_connection_status():
    hf_configured = bool(HF_TOKEN or HF_TOKEN_2 or HF_TOKEN_3)
    return [
        ("Anthropic", bool(ANTHROPIC_API_KEY), ANTHROPIC_MODEL),
        ("DeepSeek", bool(DEEPSEEK_API_KEY), DEEPSEEK_MODEL),
        ("Gemini", bool(GEMINI_API_KEY), GEMINI_MODEL),
        ("Hugging Face", hf_configured, HF_IMAGE_MODEL),
        ("Kimi", bool(KIMI_API_KEY), KIMI_MODEL),
        ("OpenAI", bool(OPENAI_API_KEY), OPENAI_MODEL),
        ("OpenRouter", bool(OPENROUTER_API_KEY), OPENROUTER_MODEL),
        ("Telegram", bool(TELEGRAM_BOT_TOKEN), "Bot API"),
        ("xAI", bool(XAI_API_KEY), XAI_MODEL),
        ("You.com", bool(YOU_API_KEY), YOU_MODEL),
    ]


def render_scheduled_tasks() -> None:
    st.markdown("**⏰ Scheduled Tasks**")
    if not DATABASE_URL:
        st.caption("Database not configured")
        return
    try:
        tasks = list_tasks(st.session_state.get("telegram_chat_id", ""), limit=15)
        if not tasks:
            st.caption("No scheduled tasks")
            return
        for task in tasks:
            due = task["due_at"].astimezone(ZoneInfo(task["timezone"] or DEFAULT_TIMEZONE))
            due_text = due.strftime("%d %b • %I:%M %p").lstrip("0")
            status = str(task["status"]).upper()
            label = clean_text(task["task_text"]).replace("\n", " ")
            if len(label) > 46:
                label = label[:43].rstrip() + "..."
            st.caption(f"**{due_text}**  •  `{status}`\n{label}")
    except Exception as exc:
        st.caption(f"Tasks unavailable: {str(exc)[:120]}")


def render_history() -> None:
    if not DATABASE_URL:
        st.caption("Database not configured")
        return
    try:
        chats = list_recent_chats(limit=15, owner_id=owner_key())
    except Exception as exc:
        st.caption(f"History unavailable: {str(exc)[:120]}")
        return
    if not chats:
        st.caption("No conversations yet")
        return
    for index, chat in enumerate(chats):
        title = clean_text(chat["title"]) or "New Chat"
        if len(title) > 45:
            title = title[:42].rstrip() + "..."
        updated = chat["updated_at"]
        updated_text = (
            updated.astimezone(ZoneInfo(DEFAULT_TIMEZONE)).strftime("%d %b, %I:%M %p").lstrip("0")
            if updated else ""
        )
        label = f"{title}\n{updated_text}" if updated_text else title
        if st.button(label, key=f"chat_history_{index}_{chat['session_key']}", use_container_width=True):
            open_history_chat(chat["session_key"])


def render_model_connections() -> None:
    connections = model_connection_status()
    connected = 0
    for name, configured, model in connections:
        if configured:
            connected += 1
            st.success(f"✓ {name}  •  {model}")
        else:
            st.caption(f"○ {name} — not connected")
    st.caption(f"{connected}/{len(connections)} connections configured")


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"## 🤖 {APP_NAME}")
        st.caption(f"v{APP_VERSION} • optimized workspace")
        st.divider()
        if st.button("＋ New Chat", use_container_width=True, type="primary"):
            start_new_chat()
        with st.expander("⏰ Scheduled Tasks", expanded=False):
            render_scheduled_tasks()
        with st.expander("🕘 History — 15 chats", expanded=True):
            render_history()
        with st.expander("🔌 Model Connections", expanded=False):
            render_model_connections()
        st.divider()
        st.subheader("AI Provider")
        providers = ["Auto", "Anthropic", "DeepSeek", "Gemini", "Kimi", "OpenAI", "OpenRouter", "xAI", "You.com"]
        current = st.session_state.get("preferred_provider", "Auto")
        st.session_state["preferred_provider"] = st.selectbox(
            "Text provider", providers,
            index=providers.index(current) if current in providers else 0,
            label_visibility="collapsed",
        )
        st.divider()
        st.subheader("Files")
        files = st.file_uploader(
            "Upload files",
            type=["txt", "md", "csv", "json", "py", "html", "xml", "yaml", "yml", "pdf", "docx"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if files:
            process_files(files)
        if st.session_state.get("uploaded_names"):
            st.caption("Loaded: " + ", ".join(st.session_state["uploaded_names"]))
        st.divider()
        st.caption("API keys remain in Render Environment Variables and are never displayed.")


def render_messages() -> None:
    for message in st.session_state.get("messages", []):
        with st.chat_message(message.get("role", "assistant")):
            kind = message.get("type", "text")
            if kind == "image" and message.get("image"):
                st.image(message["image"], use_container_width=True)
                if message.get("provider"):
                    st.caption(f"Generated by {message['provider']}" + (f" • {message['model']}" if message.get("model") else ""))
            elif kind == "image_prompt":
                st.markdown(f"🖼️ **Image request:** {clean_text(message.get('content'))}")
            else:
                st.markdown(clean_text(message.get("content")))
                if message.get("provider"):
                    st.caption(f"Model: {message['provider']} • {message.get('model', 'Unknown')}")


def generate_image_request(prompt: str) -> None:
    prompt = clean_text(prompt)
    if not prompt:
        st.warning("Image prompt empty hai.")
        return
    append_message("user", prompt, type="image_prompt")
    with st.chat_message("user"):
        st.markdown(f"🖼️ **Image request:** {prompt}")
    with st.chat_message("assistant"):
        status = thinking_status("Generating image…")
        try:
            result = generate_image(prompt=prompt)
            image_data = result.get("image")
            if not image_data:
                raise AgentError("Image provider returned no image.")
            provider = result.get("provider", "")
            model = result.get("model", "")
            append_message("assistant", "[Generated image]", type="image", image=image_data, provider=provider, model=model)
            finish_status(status, "Image ready")
            st.image(image_data, use_container_width=True)
            st.caption(f"Generated by {provider}" + (f" • {model}" if model else ""))
        except Exception as exc:
            fail_status(status, "Image generation failed")
            error = f"Image generation failed: {exc}"
            append_message("assistant", error)
            st.error(error)


def render_image_generator() -> None:
    with st.popover("🖼️ Generate Image", use_container_width=True):
        st.markdown("### Image Generator")
        st.caption("Image generation is explicit; normal chat stays text-first.")
        image_prompt = st.text_area(
            "Image prompt",
            placeholder="Example: cinematic realistic village house in Kutch at golden hour...",
            height=110,
            key="image_prompt_input",
        )
        if st.button("Generate Image", type="primary", use_container_width=True, key="generate_image_button"):
            if clean_text(image_prompt):
                generate_image_request(image_prompt)
            else:
                st.warning("Pehle image prompt likho.")


def answer_time_question() -> None:
    prompt = st.session_state.get("pending_time_prompt")
    location_key = st.session_state.get("pending_time_location")
    if not prompt or not location_key:
        return
    tz_name, location_name = TIME_LOCATIONS[location_key]
    now = datetime.now(ZoneInfo(tz_name))
    time_text = now.strftime("%I:%M %p").lstrip("0")
    date_text = now.strftime("%d %B %Y")
    answer = f"Abhi {location_name} me **{time_text}** hai.\n\n📍 Location: {location_name}\n🕒 Time zone: {tz_name}\n📅 Date: {date_text}"
    append_message("assistant", answer, provider="System Clock", model=tz_name)
    with st.chat_message("assistant"):
        st.markdown(answer)
        st.caption(f"Accurate local time • System Clock • {tz_name}")
    st.session_state["last_time_location"] = location_key
    st.session_state["pending_time_prompt"] = None
    st.session_state["pending_time_location"] = None


def render_time_location_popup() -> None:
    prompt = st.session_state.get("pending_time_prompt")
    if not prompt or st.session_state.get("pending_time_location"):
        return
    default_location = st.session_state.get("last_time_location", "India — IST")
    options = list(TIME_LOCATIONS.keys())
    default_index = options.index(default_location) if default_location in options else 0
    with st.popover("📍 Select Location for Accurate Time", use_container_width=True):
        st.markdown("**Aap kis location ka current time chahte hain?**")
        selected = st.selectbox("Location", options, index=default_index, key="time_location_selector")
        if st.button("Use This Location", type="primary", use_container_width=True, key="use_time_location"):
            st.session_state["pending_time_location"] = selected
            st.rerun()


def handle_prompt(prompt: str) -> None:
    prompt = clean_text(prompt)
    if not prompt:
        return
    with st.chat_message("user"):
        st.markdown(prompt)
    append_message("user", prompt)
    if is_time_query(prompt):
        st.session_state["pending_time_prompt"] = prompt
        st.session_state["pending_time_location"] = None
        return

    recent = st.session_state.get("recent_context", [])[-20:]
    context = {
        "user_id": get_web_user_id(),
        "memory_context": "",
        "file_context": st.session_state.get("file_context", ""),
        "recent_messages": recent,
        "preferred_provider": None if st.session_state.get("preferred_provider") == "Auto" else st.session_state.get("preferred_provider"),
        "uploaded_files": [],
    }

    with st.chat_message("assistant"):
        status = thinking_status("Thinking…")
        try:
            result = run_agent(query=prompt, context=context)
            if not result.success:
                exact_error = clean_text((result.metadata or {}).get("error")) or clean_text(result.answer) or "Agent execution failed."
                fail_status(status, "Agent failed")
                append_message("assistant", exact_error)
                st.error(exact_error)
            else:
                answer = clean_text(result.answer)
                if not answer:
                    raise AgentError("Agent returned an empty response.")
                provider = clean_text(result.provider)
                model = clean_text((result.metadata or {}).get("model"))
                append_message("assistant", answer, provider=provider, model=model)
                finish_status(status, "Response ready")
                st.markdown(answer)
                st.caption(f"Model: {provider or 'Unknown'} • {model or 'Unknown'}")
        except Exception as exc:
            fail_status(status, "AI Agent error")
            error = f"AI Agent error: {exc}"
            append_message("assistant", error)
            st.error(error)

    assistant_message = st.session_state["messages"][-1].get("content", "") if st.session_state.get("messages") else ""
    st.session_state["recent_context"].extend([
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": assistant_message},
    ])
    st.session_state["recent_context"] = st.session_state["recent_context"][-20:]
    persist_current_chat()


def main() -> None:
    initialize_state()
    render_sidebar()
    render_optimized_header(APP_NAME, APP_VERSION, "New Chat")
    render_image_generator()
    render_empty_state()
    render_messages()
    render_time_location_popup()
    if st.session_state.get("pending_time_location"):
        answer_time_question()
    prompt = st.chat_input("Message My AI Agent…")
    if prompt:
        handle_prompt(prompt)


if __name__ == "__main__":
    main()
