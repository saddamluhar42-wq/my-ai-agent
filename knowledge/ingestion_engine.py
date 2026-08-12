"""Universal Knowledge Ingestion Engine.

Acquisition is separated from normalization, chunking, embedding and storage.
This lets Ultra Legend ingest local files and external sources without coupling
knowledge storage to a particular provider.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping
import json
import re

from knowledge.ingestion import ingest_text
from knowledge.source_connectors import AutomaticSourceConnector, SourceConnectorError, SourcePayload


@dataclass(slots=True)
class IngestionItem:
    content: str
    source: str
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    content_type: str = "text"


@dataclass(slots=True)
class IngestionResult:
    accepted: int = 0
    skipped: int = 0
    failed: int = 0
    records: list[Any] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class UniversalIngestionEngine:
    """Normalize heterogeneous knowledge into the existing RAG pipeline."""

    SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".json", ".csv", ".log", ".pdf"}

    def __init__(self, *, github_token: str | None = None) -> None:
        self.sources = AutomaticSourceConnector(github_token=github_token)

    def normalize(self, item: IngestionItem) -> IngestionItem | None:
        text = re.sub(r"\n{3,}", "\n\n", item.content.replace("\x00", " ")).strip()
        if not text:
            return None
        metadata = dict(item.metadata)
        metadata.setdefault("content_hash", sha256(text.encode("utf-8")).hexdigest())
        metadata.setdefault("content_type", item.content_type)
        return IngestionItem(text, item.source, item.title, metadata, item.content_type)

    def ingest_items(self, items: Iterable[IngestionItem]) -> IngestionResult:
        result = IngestionResult()
        seen: set[str] = set()
        for raw in items:
            item = self.normalize(raw)
            if item is None:
                result.skipped += 1
                continue
            digest = item.metadata["content_hash"]
            if digest in seen:
                result.skipped += 1
                continue
            seen.add(digest)
            try:
                stored = ingest_text(
                    item.content,
                    title=item.title or item.source,
                    source_type=item.content_type,
                    source_name=item.source,
                    source_url=item.source if item.source.startswith(("http://", "https://")) else None,
                    metadata=item.metadata,
                )
                result.accepted += stored
                result.records.append(stored)
            except Exception as exc:
                result.failed += 1
                result.errors.append(f"{item.source}: {exc}")
        return result

    def ingest_file(self, path: str | Path, *, source: str | None = None) -> IngestionResult:
        file_path = Path(path).expanduser().resolve()
        if file_path.suffix.lower() == ".pdf":
            payload = self.sources.pdf.fetch(file_path)
            return self.ingest_payload(payload)
        if file_path.suffix.lower() not in self.SUPPORTED_SUFFIXES:
            raise ValueError(f"Unsupported file type: {file_path.suffix or 'unknown'}")
        raw = file_path.read_text(encoding="utf-8", errors="replace")
        if file_path.suffix.lower() == ".json":
            try:
                raw = json.dumps(json.loads(raw), ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                pass
        return self.ingest_items([IngestionItem(raw, source or str(file_path), file_path.name, {"path": str(file_path)}, file_path.suffix.lower().lstrip("."))])

    def ingest_source(self, source: str | Path, *, media_analysis: str | None = None) -> IngestionResult:
        """Auto-detect and ingest a URL, GitHub target, PDF, photo or video."""
        try:
            payload = self.sources.fetch(source, media_analysis=media_analysis)
        except SourceConnectorError as exc:
            return IngestionResult(failed=1, errors=[str(exc)])
        return self.ingest_payload(payload)

    def ingest_payload(self, payload: SourcePayload) -> IngestionResult:
        return self.ingest_items([
            IngestionItem(
                content=payload.content,
                source=payload.source,
                title=payload.title,
                metadata=payload.metadata,
                content_type=payload.source_type,
            )
        ])

    def ingest_mapping(self, data: Mapping[str, Any], *, source: str) -> IngestionResult:
        text = json.dumps(dict(data), ensure_ascii=False, indent=2, default=str)
        return self.ingest_items([IngestionItem(text, source, content_type="json")])
