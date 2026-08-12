"""UI experience layer for the Streamlit agent."""
from __future__ import annotations

import time
import streamlit as st

CSS = r"""
<style>
:root {
  --agent-radius: 18px;
  --agent-border: rgba(128,128,128,.16);
  --agent-muted: rgba(128,128,128,.72);
}
.block-container { max-width: 1320px; padding-top: 1rem; padding-bottom: 6rem; }
[data-testid="stSidebar"] { border-right: 1px solid var(--agent-border); background: rgba(18,18,22,.98); }
[data-testid="stSidebar"] .block-container { padding: .9rem .75rem 1rem; }
[data-testid="stSidebar"] [data-testid="stExpander"] { border: 1px solid var(--agent-border); border-radius: 14px; margin: .45rem 0; }
[data-testid="stSidebar"] .stButton button { border-radius: 12px; min-height: 2.35rem; }
[data-testid="stChatMessage"] { border: 1px solid var(--agent-border); border-radius: var(--agent-radius); padding: .9rem 1rem; margin: .55rem 0; }
[data-testid="stChatMessageContent"] { line-height: 1.65; }
[data-testid="stChatInput"] { padding-bottom: .6rem; }
[data-testid="stChatInput"] textarea { border-radius: 18px !important; }
[data-testid="stStatusWidget"] { border-radius: 14px; border: 1px solid var(--agent-border); }
[data-testid="stMetric"] { border: 1px solid var(--agent-border); border-radius: 16px; padding: .8rem 1rem; background: rgba(128,128,128,.035); }
.stButton button, .stDownloadButton button { border-radius: 12px; }
.stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] > div { border-radius: 12px; }
.agent-header { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:.8rem; padding:.25rem 0; }
.agent-title { font-size:1.9rem; font-weight:780; letter-spacing:-.035em; margin:0; }
.agent-subtitle { color:var(--agent-muted); font-size:.84rem; margin-top:.18rem; }
.agent-chip { display:inline-flex; align-items:center; gap:.35rem; border:1px solid var(--agent-border); border-radius:999px; padding:.32rem .72rem; font-size:.75rem; color:var(--agent-muted); }
.agent-empty { text-align:center; padding:15vh 1rem 18vh; }
.agent-empty-title { font-size:1.65rem; font-weight:720; letter-spacing:-.025em; margin-bottom:.4rem; }
.agent-empty-text { color:var(--agent-muted); font-size:.92rem; }
.agent-section-title { font-size:1.05rem; font-weight:700; margin:.5rem 0; }
@media (max-width: 800px) {
  .block-container { padding:.65rem .65rem 5rem; }
  .agent-title { font-size:1.45rem; }
  .agent-header { align-items:flex-start; }
  .agent-chip { display:none; }
  [data-testid="stChatMessage"] { padding:.75rem; }
}
</style>
"""

def apply() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

def render_header(app_name: str, version: str, chat_title: str) -> None:
    title = st.session_state.get("chat_title") or chat_title
    st.markdown(
        f'<div class="agent-header"><div><div class="agent-title">{app_name}</div>'
        f'<div class="agent-subtitle">AI workspace · v{version} · ready</div></div>'
        f'<div class="agent-chip">{title}</div></div>',
        unsafe_allow_html=True,
    )

def render_empty_state() -> None:
    if st.session_state.get("messages"):
        return
    st.markdown(
        '<div class="agent-empty"><div class="agent-empty-title">What do you want to get done?</div>'
        '<div class="agent-empty-text">Ask, research, code, analyze files, generate images, or schedule a task.</div></div>',
        unsafe_allow_html=True,
    )

def thinking_status(label: str = "Working…"):
    return st.status(label, state="running", expanded=False)

def finish_status(status, label: str = "Response ready") -> None:
    status.update(label=label, state="complete", expanded=False)

def fail_status(status, label: str = "Response failed") -> None:
    status.update(label=label, state="error", expanded=True)

def elapsed_text(start: float) -> str:
    return f"{time.monotonic() - start:.1f}s"
