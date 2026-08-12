from __future__ import annotations

import streamlit as st

from plugins.coder import plugin as coder_plugin
from plugins.manager import fetch_manifest, plugin_payload

st.set_page_config(page_title="Plugin Hub", page_icon=":material/extension:", layout="wide")

st.markdown("""
<style>
.plugin-hero { padding:1.2rem 0 .7rem; }
.plugin-hero h1 { margin:0; letter-spacing:-.035em; }
.plugin-hero p { color:rgba(128,128,128,.78); margin:.25rem 0 0; }
.plugin-card { border:1px solid rgba(128,128,128,.18); border-radius:18px; padding:1rem; min-height:145px; }
.plugin-card h3 { margin:0 0 .25rem; }
.plugin-pill { display:inline-block; border:1px solid rgba(128,128,128,.2); border-radius:999px; padding:.2rem .55rem; margin:.2rem .2rem 0 0; font-size:.75rem; }
</style>
""", unsafe_allow_html=True)

if "external_plugins" not in st.session_state:
    st.session_state["external_plugins"] = []

st.markdown('<div class="plugin-hero"><h1>🧩 Plugin Hub</h1><p>Connect tools only when the agent needs them. Keep the core lightweight and fast.</p></div>', unsafe_allow_html=True)

connected_count = int(coder_plugin.connected) + len(st.session_state["external_plugins"])
col1, col2, col3 = st.columns(3)
col1.metric("Available plugins", 1 + len(st.session_state["external_plugins"]))
col2.metric("Connected", connected_count)
col3.metric("Coder status", "Online" if coder_plugin.connected else "Needs endpoint")

st.divider()

st.subheader("Available tools")
card = st.container(border=True)
with card:
    left, right = st.columns([3, 1])
    with left:
        st.markdown("### 🧑‍💻 Coder")
        st.caption("External sandbox for coding, review, debugging and repository tasks.")
        for capability in coder_plugin.capabilities:
            st.markdown(f'<span class="plugin-pill">{capability.replace("_", " ").title()}</span>', unsafe_allow_html=True)
    with right:
        st.metric("Status", "Connected" if coder_plugin.connected else "Offline")

if coder_plugin.connected:
    st.success("Coder sandbox connected over HTTPS.")
else:
    st.warning("Coder is configured for external HTTPS execution but is not connected. Set CODER_PLUGIN_ENDPOINT in Render Environment.")

st.divider()

connect_tab, test_tab, connected_tab = st.tabs(["➕ Connect plugin", "🧪 Test Coder", "🔗 Connected"])

with connect_tab:
    st.markdown("#### Add an external plugin")
    st.caption("Only HTTPS plugin manifests are accepted. The core agent never downloads plugin source code.")
    manifest_url = st.text_input("Manifest URL", placeholder="https://example.com/.well-known/agent-plugin.json")
    if st.button("Connect plugin", type="primary", use_container_width=True):
        if not manifest_url.strip():
            st.error("Enter a manifest URL.")
        else:
            try:
                manifest = fetch_manifest(manifest_url.strip())
                payload = plugin_payload(manifest)
                existing = [p for p in st.session_state["external_plugins"] if p["endpoint"] != payload["endpoint"]]
                existing.append(payload)
                st.session_state["external_plugins"] = existing
                st.success(f"Connected {manifest.name} v{manifest.version}")
            except Exception as exc:
                st.error(f"Connection failed: {exc}")

with test_tab:
    st.markdown("#### Run a real Coder request")
    capability = st.selectbox("Capability", list(coder_plugin.capabilities), label_visibility="collapsed")
    prompt = st.text_area("Task", placeholder="Example: Review this Python function for bugs and suggest a safe fix.", height=150, label_visibility="collapsed")
    if st.button("Run Coder", type="primary", disabled=not coder_plugin.connected, use_container_width=True):
        if not prompt.strip():
            st.error("Enter a task first.")
        else:
            with st.spinner("Running in the external sandbox…"):
                try:
                    result = coder_plugin.run(capability, prompt.strip())
                    st.success("Execution completed")
                    st.json(result)
                except Exception as exc:
                    st.error(f"Execution failed: {exc}")
    if not coder_plugin.connected:
        st.caption("Test is disabled until the external Coder endpoint is connected.")

with connected_tab:
    plugins = st.session_state["external_plugins"]
    if not plugins:
        st.info("No additional external plugins connected.")
    else:
        for item in plugins:
            with st.container(border=True):
                st.markdown(f"### {item['name']} · v{item['version']}")
                if item.get("description"):
                    st.caption(item["description"])
                st.write("Capabilities:", ", ".join(item.get("capabilities", [])) or "None declared")
                st.caption(item["endpoint"])

st.divider()
st.caption("Security: HTTPS only · JSON requests only · plugin source is never downloaded or executed by the agent.")
