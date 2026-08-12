"""Source quality heuristics used by Universal Knowledge retrieval."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple
from urllib.parse import urlparse

TRUST_BY_TYPE = {
    "official": 0.95,
    "primary": 0.93,
    "academic": 0.92,
    "documentation": 0.90,
    "government": 0.95,
    "research": 0.90,
    "news": 0.75,
    "community": 0.60,
    "manual": 0.55,
    "unknown": 0.45,
}


def assess_source(
    *,
    source_type: str = "unknown",
    source_name: str = "",
    source_url: Optional[str] = None,
) -> Tuple[float, float, dict]:
    kind = str(source_type or "unknown").strip().lower()
    trust = TRUST_BY_TYPE.get(kind, TRUST_BY_TYPE["unknown"])
    host = ""
    if source_url:
        try:
            host = urlparse(source_url).netloc.lower()
        except Exception:
            host = ""
    if host.endswith(".gov") or ".gov." in host:
        trust = max(trust, 0.95)
    elif host.endswith(".edu") or ".edu." in host:
        trust = max(trust, 0.90)
    elif host:
        trust = min(1.0, trust + 0.02)

    freshness = 1.0
    now = datetime.now(timezone.utc).isoformat()
    return trust, freshness, {
        "status": "heuristic_verified",
        "source_type": kind,
        "source_name": str(source_name or ""),
        "host": host,
        "assessed_at": now,
        "note": "Trust is a retrieval signal, not proof of factual correctness.",
    }


def rank_score(relevance: float, trust: float, freshness: float) -> float:
    return (float(relevance) * 0.55) + (float(trust) * 0.30) + (float(freshness) * 0.15)
