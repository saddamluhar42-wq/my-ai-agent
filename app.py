from __future__ import annotations

import io
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

from agent.core import run_agent
from ai.agent import AgentError, generate_image
from config import (
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL, DEEPSEEK_API_KEY, DEEPSEEK_MODEL,
    GEMINI_API_KEY, GEMINI_MODEL, KIMI_API_KEY, KIMI_MODEL,
    OPENAI_API_KEY, OPENAI_MODEL, OPENROUTER_API_KEY, OPENROUTER_MODEL,
    XAI_API_KEY, XAI_MODEL, YOU_API_KEY, YOU_MODEL,
    HF_TOKEN, HF_TOKEN_2, HF_TOKEN_3, HF_IMAGE_MODEL, TELEGRAM_BOT_TOKEN,
)
from providers.video.bootstrap import initialize_video_system
from providers.video.manager import generate_video

APP_NAME = "My AI Agent"
APP_VERSION = "1.3.4"
MAX_FILE_SIZE_MB = 20

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

@st.cache_resource
def boot_video_system():
    try:
        manager = initialize_video_system()
        return manager, ""
    except Exception as exc:
        return None, str(exc)

def initialize_state() -> None:
    defaults = {
        "messages": [], "recent_context": [], "preferred_provider": "Auto",
        "file_context": "", "uploaded_names": [], "history": [],
        "pending_time_prompt": None, "pending_time_location": None,
        "last_time_location": "India — IST",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def safe_read_file(uploaded_file) -> str:
    name = uploaded_file.name.lower(); raw = uploaded_file.getvalue()
    if len(raw) > MAX_FILE_SIZE_MB * 1024 * 1024: raise ValueError(f"File exceeds {MAX_FILE_SIZE_MB} MB limit.")
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(raw)).pages)
    if name.endswith(".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(io.BytesIO(raw)).paragraphs)
    return raw.decode("utf-8", errors="replace")

def process_files(files) -> None:
    if not files: return
    chunks, names = [], []
    for uploaded in files:
        try: names.append(uploaded.name); chunks.append(f"FILE: {uploaded.name}\n{safe_read_file(uploaded)[:50000]}")
        except Exception as exc: st.error(f"{uploaded.name}: {exc}")
    if chunks: st.session_state["file_context"] = "\n\n---\n\n".join(chunks); st.session_state["uploaded_names"] = names

def clean_text(value: object) -> str: return str(value or "").strip()

def is_time_query(prompt: str) -> bool:
    text = prompt.lower()
    phrases = (
        "time kya", "time bata", "kitne baje", "kitna time", "abhi time", "current time",
        "local time", "what time", "tell me the time", "time now", "samay kya", "samay bata",
        "waqt kya", "waqt bata", "clock time", "abhi kitne baje",
    )
    return any(phrase in text for phrase in phrases) or ("time" in text and any(word in text for word in ("abhi", "current", "local", "now")))

def answer_time_question() -> None:
    prompt = st.session_state.get("pending_time_prompt")
    location_key = st.session_state.get("pending_time_location")
    if not prompt or not location_key: return
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

def model_connection_status():
    hf_configured = bool(HF_TOKEN or HF_TOKEN_2 or HF_TOKEN_3)
    return [("Anthropic", bool(ANTHROPIC_API_KEY), ANTHROPIC_MODEL), ("DeepSeek", bool(DEEPSEEK_API_KEY), DEEPSEEK_MODEL), ("Gemini", bool(GEMINI_API_KEY), GEMINI_MODEL), ("Hugging Face", hf_configured, HF_IMAGE_MODEL), ("Kimi", bool(KIMI_API_KEY), KIMI_MODEL), ("OpenAI", bool(OPENAI_API_KEY), OPENAI_MODEL), ("OpenRouter", bool(OPENROUTER_API_KEY), OPENROUTER_MODEL), ("Telegram", bool(TELEGRAM_BOT_TOKEN), "Bot API"), ("xAI", bool(XAI_API_KEY), XAI_MODEL), ("You.com", bool(YOU_API_KEY), YOU_MODEL)]

def add_history_entry(prompt: str) -> None:
    prompt = clean_text(prompt)
    if not prompt: return
    history = st.session_state.setdefault("history", []); history[:] = [item for item in history if item != prompt]; history.insert(0, prompt); del history[20:]

def render_history() -> None:
    history = st.session_state.get("history", [])
    if not history: st.caption("No conversations yet"); return
    for index, item in enumerate(history):
        label = item if len(item) <= 42 else item[:39].rstrip() + "..."
        if st.button(label, key=f"history_{index}", use_container_width=True): st.session_state["history_selected"] = item; st.info("History item selected. Start a new message to continue this topic.")

def render_model_connections() -> None:
    connections = model_connection_status(); connected = 0
    for name, configured, model in connections:
        if configured: connected += 1; st.success(f"✓ {name}  •  {model}")
        else: st.caption(f"○ {name} — not connected")
    st.caption(f"{connected}/{len(connections)} connections configured")

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"## 🤖 {APP_NAME}"); st.caption(f"v{APP_VERSION} • Streamlit direct mode"); st.divider()
        if st.button("＋ New Chat", use_container_width=True, type="primary"):
            st.session_state["messages"]=[]; st.session_state["recent_context"]=[]; st.session_state["file_context"]=""; st.session_state["uploaded_names"]=[]; st.session_state["pending_time_prompt"]=None; st.session_state["pending_time_location"]=None; st.rerun()
        with st.expander("🕘 History", expanded=True): render_history()
        with st.expander("🔌 Model Connections", expanded=True): render_model_connections()
        st.divider(); st.subheader("AI Provider")
        providers=["Auto","Anthropic","DeepSeek","Gemini","Kimi","OpenAI","OpenRouter","xAI","You.com"]
        current=st.session_state.get("preferred_provider","Auto"); st.session_state["preferred_provider"]=st.selectbox("Text provider",providers,index=providers.index(current) if current in providers else 0,label_visibility="collapsed")
        st.divider(); st.subheader("Files")
        files=st.file_uploader("Upload files",type=["txt","md","csv","json","py","html","xml","yaml","yml","pdf","docx"],accept_multiple_files=True,label_visibility="collapsed")
        if files: process_files(files)
        if st.session_state.get("uploaded_names"): st.caption("Loaded: "+", ".join(st.session_state["uploaded_names"]))
        st.divider(); st.caption("API keys remain in Render Environment Variables and are never displayed.")

def render_header() -> None: st.title("My AI Agent"); st.caption("Chat • Image Generation • Video Generation")
def append_message(role: str, content: str, **extra) -> None: item={"role":role,"content":content}; item.update(extra); st.session_state["messages"].append(item)

def render_messages() -> None:
    for message in st.session_state.get("messages",[]):
        with st.chat_message(message.get("role","assistant")):
            kind=message.get("type","text")
            if kind=="image" and message.get("image"):
                st.image(message["image"],use_container_width=True)
                if message.get("provider"): st.caption(f"Generated by {message['provider']}"+(f" • {message['model']}" if message.get('model') else ""))
            elif kind=="video" and message.get("video_path"):
                path=Path(message["video_path"])
                if path.exists(): st.video(str(path)); st.download_button("Download video",path.read_bytes(),file_name=path.name,mime="video/mp4",key=f"download_{path.name}")
                else: st.error("Generated video file is no longer available.")
            else:
                st.markdown(clean_text(message.get("content")))
                if message.get("provider"): st.caption(f"Model: {message['provider']} • {message.get('model','Unknown')}")

def generate_image_request(prompt: str) -> None:
    with st.chat_message("user"): st.markdown(prompt)
    append_message("user",prompt)
    with st.chat_message("assistant"):
        with st.spinner("Generating image..."):
            try:
                result=generate_image(prompt=prompt); image_data=result.get("image")
                if not image_data: raise AgentError("Image provider returned no image.")
                provider=result.get("provider",""); model=result.get("model",""); append_message("assistant","",type="image",image=image_data,provider=provider,model=model)
                st.image(image_data,use_container_width=True); st.caption(f"Generated by {provider}"+(f" • {model}" if model else ""))
            except Exception as exc: error=f"Image generation failed: {exc}"; append_message("assistant",error); st.error(error)

def generate_video_request(prompt: str) -> None:
    with st.chat_message("user"): st.markdown(prompt)
    append_message("user",prompt)
    with st.chat_message("assistant"):
        with st.spinner("Generating video... This can take a few minutes."):
            output_dir=Path("generated_videos"); output_dir.mkdir(parents=True,exist_ok=True); output_path=output_dir/f"video_{os.urandom(8).hex()}.mp4"; provider=None if st.session_state.get("preferred_provider","Auto")=="Auto" else st.session_state["preferred_provider"].lower()
            try:
                result=generate_video(prompt=prompt,provider=provider,output_path=str(output_path),fallback=True)
                if not isinstance(result,dict) or not result.get("success"): raise AgentError(result.get("error","Video generation failed.") if isinstance(result,dict) else "Invalid video result.")
                final_path=Path(result.get("output_path",output_path))
                if not final_path.exists(): raise AgentError("Video provider reported success but output file was not found.")
                append_message("assistant","",type="video",video_path=str(final_path),provider=result.get("provider",provider or "Auto"),model=result.get("model",""),task_id=result.get("task_id")); st.video(str(final_path)); st.download_button("Download video",final_path.read_bytes(),file_name=final_path.name,mime="video/mp4",key=f"download_now_{final_path.name}")
            except Exception as exc: error=f"Video generation failed: {exc}"; append_message("assistant",error); st.error(error)

def handle_prompt(prompt: str) -> None:
    prompt=clean_text(prompt)
    if not prompt: return
    add_history_entry(prompt); lowered=prompt.lower()
    if any(word in lowered for word in ("generate image","create image","make image","image banao","image bana do","photo banao","picture banao")): generate_image_request(prompt); return
    if any(word in lowered for word in ("generate video","create video","make video","video banao","video bana do","video generate")): generate_video_request(prompt); return
    with st.chat_message("user"): st.markdown(prompt)
    append_message("user",prompt)
    if is_time_query(prompt):
        st.session_state["pending_time_prompt"] = prompt
        st.session_state["pending_time_location"] = None
        return
    recent=st.session_state.get("recent_context",[])[-20:]; context={"user_id":None,"memory_context":"","file_context":st.session_state.get("file_context",""),"recent_messages":recent,"preferred_provider":None if st.session_state.get("preferred_provider")=="Auto" else st.session_state.get("preferred_provider"),"uploaded_files":[]}
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result=run_agent(query=prompt,context=context)
                if not result.success: raise AgentError(result.metadata.get("error","Agent execution failed."))
                answer=clean_text(result.answer)
                if not answer: raise AgentError("Agent returned an empty response.")
                provider=clean_text(result.provider); model=clean_text((result.metadata or {}).get("model")); append_message("assistant",answer,provider=provider,model=model); st.markdown(answer); st.caption(f"Model: {provider or 'Unknown'} • {model or 'Unknown'}")
            except Exception as exc: error=f"AI Agent error: {exc}"; append_message("assistant",error); st.error(error)
    st.session_state["recent_context"].extend([{"role":"user","content":prompt},{"role":"assistant","content":st.session_state["messages"][-1].get("content","")}]); st.session_state["recent_context"]=st.session_state["recent_context"][-20:]

def main() -> None:
    initialize_state(); boot_video_system(); render_sidebar(); render_header(); render_messages()
    render_time_location_popup()
    if st.session_state.get("pending_time_location"):
        answer_time_question()
    prompt=st.chat_input("Message My AI Agent...")
    if prompt: handle_prompt(prompt)

if __name__=="__main__": main()
