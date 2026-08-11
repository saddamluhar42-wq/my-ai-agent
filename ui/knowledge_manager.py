"""UI for adding persistent documents to the agent's knowledge brain."""

import streamlit as st

from knowledge.document_rag import ingest_document, initialize_document_store, install_core_bridge


def render_knowledge_manager() -> None:
    """Render the persistent Knowledge Brain controls."""
    try:
        initialize_document_store()
        install_core_bridge()
    except Exception as error:
        st.warning(f"Knowledge Brain unavailable: {str(error)[:180]}")
        return

    with st.expander("🧠 Knowledge Brain", expanded=False):
        st.caption("Upload documents once. The agent stores their text in PostgreSQL and retrieves relevant sections when answering.")
        uploaded = st.file_uploader(
            "Add knowledge",
            type=["pdf", "docx", "txt", "md", "csv", "json"],
            accept_multiple_files=True,
            key="knowledge_brain_uploads",
        )

        if uploaded and st.button("Add to Knowledge Brain", type="primary", key="knowledge_brain_add"):
            user_id = st.session_state.get("user_id")
            success = 0
            for item in uploaded:
                try:
                    result = ingest_document(
                        user_id=user_id,
                        filename=item.name,
                        data=item.getvalue(),
                        content_type=item.type or "",
                    )
                    if result.get("duplicate"):
                        st.info(f"Already added: {item.name}")
                    else:
                        success += 1
                        st.success(f"Added: {item.name} ({result['chunks']} chunks)")
                except Exception as error:
                    st.error(f"Could not add {item.name}: {str(error)[:180]}")
            if success:
                st.rerun()
