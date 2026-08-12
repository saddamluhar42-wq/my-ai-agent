"""Document-to-knowledge ingestion pipeline.

The pipeline is intentionally provider-neutral: callers provide text and source
metadata, while this module normalizes, chunks, deduplicates, scores, embeds,
and stores records in the Universal Knowledge Hub.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

from knowledge.embeddings import embed_text
from knowledge.universal_hub import upsert_knowledge
from knowledge.verification import assess_source

DEFAULT_CHUNK_SIZE = 3500
DEFAULT_OVERLAP = 350


def normalize_text(text: str) -> str:
    text = str(text or "").replace("\x00", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []
    chunk_size = max(500, int(chunk_size))
    overlap = max(0, min(int(overlap), chunk_size // 3))
    if len(text) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        if end < len(text):
            boundary = text.rfind("\n\n", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


def ingest_text(
    text: str,
    *,
    title: str = "",
    domain: str = "general",
    source_type: str = "document",
    source_name: str = "",
    source_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    embed: bool = True,
) -> int:
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        return 0

    metadata = dict(metadata or {})
    trust_score, freshness_score, verification = assess_source(
        source_type=source_type,
        source_name=source_name,
        source_url=source_url,
    )
    metadata["verification"] = verification
    metadata["chunk_count"] = len(chunks)

    stored = 0
    for index, chunk in enumerate(chunks):
        chunk_metadata = dict(metadata)
        chunk_metadata["chunk_index"] = index
        chunk_metadata["embedding_available"] = False
        if embed:
            vector = embed_text(f"{title}\n{chunk}")
            if vector:
                chunk_metadata["embedding"] = vector
                chunk_metadata["embedding_model"] = "text-embedding-004"
                chunk_metadata["embedding_available"] = True
        record_id = upsert_knowledge(
            content=chunk,
            domain=domain,
            title=f"{title} [chunk {index + 1}/{len(chunks)}]" if len(chunks) > 1 else title,
            source_type=source_type,
            source_name=source_name,
            source_url=source_url,
            trust_score=trust_score,
            freshness_score=freshness_score,
            metadata=chunk_metadata,
        )
        if record_id is not None:
            stored += 1
    return stored


def ingest_records(records: Iterable[Dict[str, Any]], *, embed: bool = True) -> int:
    total = 0
    for record in records:
        item = dict(record)
        item["embed"] = embed
        total += ingest_text(**item)
    return total
