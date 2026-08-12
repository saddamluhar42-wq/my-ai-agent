"""UI experience layer for the Streamlit agent."""
from __future__ import annotations

import time
import streamlit as st


CSS = r"""
<style>
:root { --agent-radius: 16px; }
.block-container { max-width: 1180px; padding-top: 1.1rem; padding-bottom: 7rem; }
[data-testid="stSidebar"] { border-right: 1px solid rgba(128,128,128,.18); }
[data-testid="stSidebar"] .block-container { padding-top: 1rem; padding-bottom: 1rem; }
[data-testid="stChatMessage"] { border-radius: var(--agent-radius); margin: .45rem 0; }
[data-testid="stChatMessageContent"] { line-height: 1.65; }
[data-testid="stChatInput"] { padding-bottom: .7rem; }
[data-testid="stStatusWidget"] { border-radius: 14px; }
.agent-header { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:.4rem; }
.agent-title { font-size:1.8rem; font-weight:750; letter-spacing:-.025em; margin:0; }
.agent-subtitle { opacity:.68; font-size:.88rem; margin-top:.15rem; }
.agent-chip { display:inline-flex; align-items:center; border:1px solid rgba(128,128,128,.22); border-radius:999px; padding:.28rem .65rem; font-size:.76rem; opacity:.85; }
.agent-empty { text-align:center; padding:13vh 1rem 18vh; opacity:.72; }
.agent-empty-title { font-size:1.35rem; font-weight:650; margin-bottom:.35rem; }
.agent-empty-text { font-size:.9rem; }
@media (max-width: 800px) {
  .block-container { padding-top:.7rem; padding-left:.8rem; padding-right:.8rem; }
  .agent-title { font-size:1.45rem; }
}
</style>
"""


def apply() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def render_header(app_name: str, version: str, chat_title: str) -> None:
    title = st.session_state.get("chat_title") or chat_title
    st.markdown(
        f'<div class="agent-header"><div><div class="agent-title">{app_name}</div>'
        f'<div class="agent-subtitle">AI workspace • v{version}</div></div>'
        f'<div class="agent-chip">{title}</div></div>',
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    if st.session_state.get("messages"):
        return
    st.markdown(
        '<div class="agent-empty"><div class="agent-empty-title">How can I help?</div>'
        '<div class="agent-empty-text">Ask a question, upload a file, or use Generate Image.</div></div>',
        unsafe_allow_html=True,
    )


def thinking_status(label: str = "Thinking…"):
    """Persistent status container that remains visible for the whole blocking call."""
    return st.status(label, state="running", expanded=False)


def finish_status(status, label: str = "Response ready") -> None:
    status.update(label=label, state="complete", expanded=False)


def fail_status(status, label: str = "Response failed") -> None:
    status.update(label=label, state="error", expanded=True)


def elapsed_text(start: float) -> str:
    return f"{time.monotonic() - start:.1f}s"
