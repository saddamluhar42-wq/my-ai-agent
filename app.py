from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path

import streamlit as st

from agent.core import run_agent
from ai.agent import AgentError, generate_image, is_image_generation_available
from providers.video.bootstrap import (
    get_ready_video_providers,
    get_video_system_status,
    initialize_video_system,
)
from providers.video.manager import generate_video


APP_NAME = "My AI Agent"
APP_VERSION = "1.1.0"
MAX_FILE_SIZE_MB = 20

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def boot_video_system():
    try:
        manager = initialize_video_system()
        return manager, ""
    except Exception as exc:
        return None, str(exc)


def initialize_state() -> None:
    defaults = {
        "messages": [],
        "recent_context": [],
        "preferred_provider": "Auto",
        "file_context": "",
        "uploaded_names": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def safe_read_file(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()
    if len(raw) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File exceeds {MAX_FILE_SIZE_MB} MB limit.")

    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    if name.endswith(".docx"):
        from docx import Document
        doc = Document(io.BytesIO(raw))
        return "\n".join(p.text for p in doc.paragraphs)

    return raw.decode("utf-8", errors="replace")


def process_files(files) -> None:
    if not files:
        return

    chunks = []
    names = []
    for uploaded in files:
        try:
            text = safe_read_file(uploaded)
            names.append(uploaded.name)
            chunks.append(f"FILE: {uploaded.name}\n{text[:50000]}")
        except Exception as exc:
            st.error(f"{uploaded.name}: {exc}")

    if chunks:
        st.session_state["file_context"] = "\n\n---\n\n".join(chunks)
        st.session_state["uploaded_names"] = names


def clean_text(value: object) -> str:
    return str(value or "").strip()


def render_sidebar(video_error: str) -> None:
    with st.sidebar:
        st.markdown(f"## 🤖 {APP_NAME}")
        st.caption(f"v{APP_VERSION} • Streamlit direct mode")

        st.divider()
        st.subheader("AI Provider")
        provider = st.selectbox(
            "Text provider",
            ["Auto", "Gemini", "OpenRouter", "Groq", "Cerebras", "Mistral", "Anthropic"],
            index=["Auto", "Gemini", "OpenRouter", "Groq", "Cerebras", "Mistral", "Anthropic"].index(
                st.session_state.get("preferred_provider", "Auto")
            ),
            label_visibility="collapsed",
        )
        st.session_state["preferred_provider"] = provider

        st.divider()
        st.subheader("System")
        if video_error:
            st.error(f"Video system: {video_error}")
        else:
            try:
                ready = get_ready_video_providers()
                st.success(f"Video: {len(ready)} ready") if ready else st.warning("Video: no provider ready")
                if ready:
                    st.caption(", ".join(ready))
            except Exception as exc:
                st.warning(f"Video status unavailable: {exc}")

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

        if st.button("New Chat", use_container_width=True):
            st.session_state["messages"] = []
            st.session_state["recent_context"] = []
            st.rerun()

        st.divider()
        st.caption("Render Free can sleep after inactivity. The app itself no longer depends on PostgreSQL for chat responses.")


def render_header() -> None:
    st.title("My AI Agent")
    st.caption("Chat • Image Generation • Video Generation")


def append_message(role: str, content: str, **extra) -> None:
    item = {"role": role, "content": content}
    item.update(extra)
    st.session_state["messages"].append(item)


def render_messages() -> None:
    for message in st.session_state.get("messages", []):
        role = message.get("role", "assistant")
        with st.chat_message(role):
            kind = message.get("type", "text")
            if kind == "image" and message.get("image"):
                st.image(message["image"], use_container_width=True)
                provider = message.get("provider", "")
                model = message.get("model", "")
                if provider:
                    st.caption(f"Generated by {provider}" + (f" • {model}" if model else ""))
            elif kind == "video" and message.get("video_path"):
                path = Path(message["video_path"])
                if path.exists():
                    st.video(str(path))
                    try:
                        st.download_button(
                            "Download video",
                            path.read_bytes(),
                            file_name=path.name,
                            mime="video/mp4",
                            key=f"download_{path.name}",
                        )
                    except Exception:
                        pass
                else:
                    st.error("Generated video file is no longer available.")
            else:
                st.markdown(clean_text(message.get("content")))


def generate_image_request(prompt: str) -> None:
    append_message("user", prompt)
    with st.chat_message("assistant"):
        with st.spinner("Generating image..."):
            try:
                result = generate_image(prompt=prompt)
                image_data = result.get("image")
                if not image_data:
                    raise AgentError("Image provider returned no image.")
                provider = result.get("provider", "")
                model = result.get("model", "")
                append_message("assistant", "", type="image", image=image_data, provider=provider, model=model)
                st.image(image_data, use_container_width=True)
                st.caption(f"Generated by {provider}" + (f" • {model}" if model else ""))
            except Exception as exc:
                error = f"Image generation failed: {exc}"
                append_message("assistant", error)
                st.error(error)


def generate_video_request(prompt: str) -> None:
    append_message("user", prompt)
    with st.chat_message("assistant"):
        with st.spinner("Generating video... This can take a few minutes."):
            output_dir = Path("generated_videos")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"video_{os.urandom(8).hex()}.mp4"
            provider = None if st.session_state.get("preferred_provider", "Auto") == "Auto" else st.session_state["preferred_provider"].lower()
            try:
                result = generate_video(
                    prompt=prompt,
                    provider=provider,
                    output_path=str(output_path),
                    fallback=True,
                )
                if not isinstance(result, dict) or not result.get("success"):
                    raise AgentError(result.get("error", "Video generation failed.") if isinstance(result, dict) else "Invalid video result.")
                final_path = Path(result.get("output_path", output_path))
                if not final_path.exists():
                    raise AgentError("Video provider reported success but output file was not found.")
                append_message(
                    "assistant",
                    "",
                    type="video",
                    video_path=str(final_path),
                    provider=result.get("provider", provider or "Auto"),
                    model=result.get("model", ""),
                    task_id=result.get("task_id"),
                )
                st.video(str(final_path))
                st.download_button(
                    "Download video",
                    final_path.read_bytes(),
                    file_name=final_path.name,
                    mime="video/mp4",
                    key=f"download_now_{final_path.name}",
                )
            except Exception as exc:
                error = f"Video generation failed: {exc}"
                append_message("assistant", error)
                st.error(error)


def handle_prompt(prompt: str) -> None:
    prompt = clean_text(prompt)
    if not prompt:
        return

    lowered = prompt.lower()
    image_words = ("generate image", "create image", "make image", "image banao", "image bana do", "photo banao", "picture banao")
    video_words = ("generate video", "create video", "make video", "video banao", "video bana do", "video generate")

    if any(word in lowered for word in image_words):
        generate_image_request(prompt)
        return

    if any(word in lowered for word in video_words):
        generate_video_request(prompt)
        return

    append_message("user", prompt)
    recent = st.session_state.get("recent_context", [])[-20:]
    context = {
        "user_id": None,
        "memory_context": "",
        "file_context": st.session_state.get("file_context", ""),
        "recent_messages": recent,
        "preferred_provider": None if st.session_state.get("preferred_provider") == "Auto" else st.session_state.get("preferred_provider"),
        "uploaded_files": [],
    }

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = run_agent(query=prompt, context=context)
                if not result.success:
                    raise AgentError(result.metadata.get("error", "Agent execution failed."))
                answer = clean_text(result.answer)
                if not answer:
                    raise AgentError("Agent returned an empty response.")
                append_message(
                    "assistant",
                    answer,
                    provider=result.provider,
                    model=(result.metadata or {}).get("model", ""),
                )
                st.markdown(answer)
            except Exception as exc:
                error = f"AI Agent error: {exc}"
                append_message("assistant", error)
                st.error(error)

    st.session_state["recent_context"].extend([
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": st.session_state["messages"][-1].get("content", "")},
    ])
    st.session_state["recent_context"] = st.session_state["recent_context"][-20:]


def main() -> None:
    initialize_state()
    _, video_error = boot_video_system()
    render_sidebar(video_error)
    render_header()
    render_messages()

    prompt = st.chat_input("Message My AI Agent...")
    if prompt:
        handle_prompt(prompt)


if __name__ == "__main__":
    main()
