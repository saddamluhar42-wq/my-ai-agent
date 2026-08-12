"""Universal Knowledge Ingestion Engine.

Provider-agnostic ingestion orchestration for text, URLs, local files and
structured records. It deliberately keeps acquisition separate from storage
so future web/file/API connectors can plug into the same pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping
import json
import re

from knowledge.ingestion import ingest_document


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
    """Normalize heterogeneous knowledge into the existing ingestion pipeline."""

    SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".json", ".csv", ".log"}

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
                record = ingest_document(
                    text=item.content,
                    source=item.source,
                    title=item.title,
                    metadata=item.metadata,
                )
                result.accepted += 1
                result.records.append(record)
            except Exception as exc:  # connector failures must not stop a batch
                result.failed += 1
                result.errors.append(f"{item.source}: {exc}")
        return result

    def ingest_file(self, path: str | Path, *, source: str | None = None) -> IngestionResult:
        file_path = Path(path)
        if file_path.suffix.lower() not in self.SUPPORTED_SUFFIXES:
            raise ValueError(f"Unsupported file type: {file_path.suffix or 'unknown'}")
        raw = file_path.read_text(encoding="utf-8", errors="replace")
        if file_path.suffix.lower() == ".json":
            try:
                raw = json.dumps(json.loads(raw), ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                pass
        return self.ingest_items([
            IngestionItem(
                content=raw,
                source=source or str(file_path.resolve()),
                title=file_path.name,
                metadata={"path": str(file_path.resolve())},
                content_type=file_path.suffix.lower().lstrip("."),
            )
        )

    def ingest_mapping(self, data: Mapping[str, Any], *, source: str) -> IngestionResult:
        text = json.dumps(dict(data), ensure_ascii=False, indent=2, default=str)
        return self.ingest_items([IngestionItem(text, source, content_type="json")])
