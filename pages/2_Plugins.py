from __future__ import annotations

import streamlit as st

from plugins.coder import plugin as coder_plugin
from plugins.manager import fetch_manifest, plugin_payload

st.set_page_config(page_title="Plugins", page_icon="🔌", layout="wide")
st.title("🔌 Plugin Manager")
st.caption("Connect external HTTPS plugins without putting heavy engineering into the core agent.")

if "external_plugins" not in st.session_state:
    st.session_state["external_plugins"] = []

st.subheader("Built-in external plugins")
st.json({
    "name": coder_plugin.name,
    "version": coder_plugin.version,
    "capabilities": list(coder_plugin.capabilities),
    "execution": "disabled; use a separate sandbox plugin",
})

st.divider()
st.subheader("Connect external plugin")
manifest_url = st.text_input("Plugin manifest URL", placeholder="https://example.com/.well-known/agent-plugin.json")
if st.button("Connect Plugin", type="primary"):
    try:
        manifest = fetch_manifest(manifest_url)
        payload = plugin_payload(manifest)
        existing = [p for p in st.session_state["external_plugins"] if p["endpoint"] != payload["endpoint"]]
        existing.append(payload)
        st.session_state["external_plugins"] = existing
        st.success(f"Connected: {manifest.name} v{manifest.version}")
    except Exception as exc:
        st.error(f"Plugin connection failed: {exc}")

st.divider()
st.subheader("Connected external plugins")
plugins = st.session_state["external_plugins"]
if not plugins:
    st.info("No external plugins connected yet.")
else:
    for item in plugins:
        with st.container(border=True):
            st.markdown(f"**{item['name']}** · v{item['version']}")
            if item.get("description"):
                st.caption(item["description"])
            st.write("Capabilities:", ", ".join(item.get("capabilities", [])) or "None declared")
            st.caption(item["endpoint"])

st.info("Security: only HTTPS manifests/endpoints are accepted. The manager does not download or execute arbitrary plugin source code.")
