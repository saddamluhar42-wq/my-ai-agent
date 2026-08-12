from __future__ import annotations

import streamlit as st

from plugins.upwork_job_hunter import DEFAULT_SKILLS, draft_proposal, score_job

st.set_page_config(page_title="Upwork Job Hunter", page_icon="💼", layout="wide")

st.title("💼 Upwork Job Hunter")
st.caption("Analyze jobs obtained through permitted Upwork access, score the fit, and draft a proposal. Final submission remains manual.")

with st.sidebar:
    st.subheader("Target skills")
    selected = st.multiselect("Skills", DEFAULT_SKILLS, default=["excel", "power bi", "sql", "data analysis", "python"])
    freelancer_name = st.text_input("Your display name", value="")

col1, col2 = st.columns(2)
with col1:
    title = st.text_input("Job title", placeholder="Excel / Power BI Sales Dashboard")
    budget = st.text_input("Budget", placeholder="$80–150")
with col2:
    source = st.text_input("Source / Job URL", placeholder="Paste the permitted job URL or source reference")
    st.caption("The app does not scrape pages, bypass CAPTCHA, or auto-submit applications.")

description = st.text_area("Job description", height=260, placeholder="Paste the job description here…")

if st.button("Analyze Job", type="primary", use_container_width=True):
    if not title.strip() and not description.strip():
        st.warning("Job title ya description enter karo.")
    else:
        result = score_job(title, description, selected, budget)
        st.session_state["upwork_score"] = result
        st.session_state["upwork_title"] = title
        st.session_state["upwork_description"] = description

result = st.session_state.get("upwork_score")
if result:
    st.divider()
    a, b, c = st.columns(3)
    a.metric("Match Score", f"{result.score}/100")
    b.metric("Decision", result.label)
    c.metric("Matched Skills", len(result.matched_skills))

    left, right = st.columns(2)
    with left:
        st.subheader("Skill Analysis")
        st.write("**Matched:**", ", ".join(result.matched_skills) or "None")
        st.write("**Missing:**", ", ".join(result.missing_skills) or "None")
    with right:
        st.subheader("Signals")
        st.write("**Budget:**", result.budget_signal)
        for note in result.notes:
            st.write("•", note)

    st.subheader("Proposal Draft")
    proposal = draft_proposal(st.session_state["upwork_title"], st.session_state["upwork_description"], result, freelancer_name)
    edited = st.text_area("Review and edit before using", value=proposal, height=260)
    st.download_button("Download Proposal", edited, file_name="upwork_proposal.txt", mime="text/plain", use_container_width=True)

st.divider()
st.info("API access, OAuth, and any future Upwork connector should be added only after Upwork approves the required API access. Until then, paste permitted job data here for analysis.")
