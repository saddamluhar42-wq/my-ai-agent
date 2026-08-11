"""Persistent document knowledge store and lightweight RAG retrieval."""

from __future__ import annotations

import hashlib
import io
import re
from typing import Any

from database.connection import execute


SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    filename TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    content_type TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, file_hash)
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    search_text TSVECTOR GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_search
ON knowledge_chunks USING GIN(search_text);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_user
ON knowledge_documents(user_id);
"""


def initialize_document_store() -> None:
    for statement in SCHEMA.split(";"):
        statement = statement.strip()
        if statement:
            execute(statement, fetch=None)


def _extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if name.endswith(".docx"):
        from docx import Document
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    if name.endswith((".txt", ".md", ".csv", ".json")):
        return data.decode("utf-8", errors="replace")
    raise ValueError("Supported knowledge files: PDF, DOCX, TXT, MD, CSV, JSON")


def _chunks(text: str, size: int = 1400, overlap: int = 180) -> list[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    result = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunk = text[start:end].strip()
        if chunk:
            result.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return result


def ingest_document(user_id: int | None, filename: str, data: bytes, content_type: str = "") -> dict[str, Any]:
    initialize_document_store()
    text = _extract_text(filename, data)
    chunks = _chunks(text)
    if not chunks:
        raise ValueError("No readable text was found in the document.")

    file_hash = hashlib.sha256(data).hexdigest()
    existing = execute(
        "SELECT id FROM knowledge_documents WHERE user_id = %s AND file_hash = %s LIMIT 1",
        (user_id, file_hash), fetch="one"
    )
    if existing:
        return {"document_id": existing[0], "filename": filename, "chunks": 0, "duplicate": True}

    row = execute(
        """
        INSERT INTO knowledge_documents(user_id, filename, file_hash, content_type)
        VALUES (%s, %s, %s, %s) RETURNING id
        """,
        (user_id, filename, file_hash, content_type), fetch="one"
    )
    document_id = row[0]
    for index, chunk in enumerate(chunks):
        execute(
            "INSERT INTO knowledge_chunks(document_id, chunk_index, content) VALUES (%s, %s, %s)",
            (document_id, index, chunk), fetch=None
        )
    return {"document_id": document_id, "filename": filename, "chunks": len(chunks), "duplicate": False}


def search_documents(user_id: int | None, query: str, limit: int = 6) -> list[dict[str, Any]]:
    initialize_document_store()
    query = re.sub(r"[^\w\s-]", " ", query or "", flags=re.UNICODE).strip()
    if not query:
        return []
    limit = max(1, min(int(limit), 12))
    rows = execute(
        """
        SELECT d.filename, c.content,
               ts_rank_cd(c.search_text, plainto_tsquery('simple', %s)) AS score
        FROM knowledge_chunks c
        JOIN knowledge_documents d ON d.id = c.document_id
        WHERE d.user_id = %s
          AND c.search_text @@ plainto_tsquery('simple', %s)
        ORDER BY score DESC, c.id DESC
        LIMIT %s
        """,
        (query, user_id, query, limit), fetch="all"
    )
    return [{"filename": row[0], "content": row[1], "score": float(row[2] or 0)} for row in rows]


def format_document_context(results: list[dict[str, Any]]) -> str:
    if not results:
        return ""
    lines = ["DOCUMENT KNOWLEDGE (retrieved from the user's persistent knowledge base):"]
    for item in results:
        lines.append(f"\nSource: {item['filename']}\n{item['content']}")
    return "\n".join(lines)


def install_core_bridge() -> None:
    """Patch the existing agent core so document RAG participates automatically."""
    try:
        import agent.core as core
        original = core.build_knowledge_context
        if getattr(original, "_document_rag_bridge", False):
            return

        def bridged_build_knowledge_context(user_id, query, limit=20):
            base = original(user_id=user_id, query=query, limit=limit)
            docs = format_document_context(search_documents(user_id=user_id, query=query, limit=6))
            if docs:
                return f"{base}\n\n{docs}" if base else docs
            return base

        bridged_build_knowledge_context._document_rag_bridge = True
        core.build_knowledge_context = bridged_build_knowledge_context
    except Exception:
        # The normal agent remains usable even if the optional bridge cannot load.
        return
