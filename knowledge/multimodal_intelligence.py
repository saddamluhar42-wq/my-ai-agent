"""Advanced multimodal evidence normalization and temporal reasoning."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Evidence:
    modality: str
    content: str
    confidence: float = 0.5
    timestamp: Optional[float] = None
    source: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultimodalInsight:
    summary: str
    evidence: List[Evidence]
    observations: List[str]
    inferences: List[str]
    conflicts: List[str]
    confidence: float


class MultimodalIntelligence:
    """Fuse pre-extracted text/image/audio/video evidence without inventing facts."""

    def __init__(self, max_evidence: int = 100):
        self.max_evidence = max(1, min(500, max_evidence))

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def normalize(self, raw: List[Dict[str, Any]]) -> List[Evidence]:
        output: List[Evidence] = []
        for item in raw[: self.max_evidence]:
            modality = str(item.get("modality", "unknown")).lower().strip() or "unknown"
            content = str(item.get("content", "")).strip()
            if not content:
                continue
            output.append(Evidence(
                modality=modality,
                content=content,
                confidence=self._clamp(item.get("confidence", 0.5)),
                timestamp=item.get("timestamp"),
                source=item.get("source"),
                attributes=dict(item.get("attributes") or {}),
            ))
        return output

    def fuse(self, evidence: List[Evidence]) -> MultimodalInsight:
        if not evidence:
            return MultimodalInsight("No usable multimodal evidence.", [], [], [], [], 0.0)
        observations = [f"[{e.modality}] {e.content}" for e in evidence]
        conflicts: List[str] = []
        by_key: Dict[str, List[Evidence]] = {}
        for e in evidence:
            key = e.attributes.get("entity")
            if key:
                by_key.setdefault(str(key).lower(), []).append(e)
        for entity, items in by_key.items():
            values = {str(i.attributes.get("value")) for i in items if i.attributes.get("value") is not None}
            if len(values) > 1:
                conflicts.append(f"Conflicting evidence for {entity}: {sorted(values)}")
        confidence = sum(e.confidence for e in evidence) / len(evidence)
        if conflicts:
            confidence *= 0.75
        summary = " | ".join(observations[:8])
        return MultimodalInsight(summary, evidence, observations, [], conflicts, self._clamp(confidence))

    def temporal_order(self, evidence: List[Evidence]) -> List[Evidence]:
        """Return timestamped evidence first in chronological order; undated evidence follows."""
        return sorted(evidence, key=lambda e: (e.timestamp is None, e.timestamp if e.timestamp is not None else 0.0))

    def compare_modalities(self, evidence: List[Evidence]) -> Dict[str, Any]:
        grouped: Dict[str, List[Evidence]] = {}
        for item in evidence:
            grouped.setdefault(item.modality, []).append(item)
        return {
            "modalities": {k: len(v) for k, v in grouped.items()},
            "agreement": len(grouped) > 1 and not self.fuse(evidence).conflicts,
            "confidence": self.fuse(evidence).confidence if evidence else 0.0,
        }
