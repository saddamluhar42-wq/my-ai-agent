"""Controlled self-improvement telemetry and evidence evaluation."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from database.connection import execute


SCHEMA = """
CREATE TABLE IF NOT EXISTS intelligence_runs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    provider TEXT,
    model TEXT,
    skill TEXT,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.50,
    verification_status TEXT NOT NULL DEFAULT 'unverified',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS intelligence_feedback (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES intelligence_runs(id) ON DELETE CASCADE,
    rating INTEGER,
    feedback TEXT,
    corrected_answer TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def initialize_evolution_store() -> None:
    for statement in SCHEMA.split(";"):
        statement = statement.strip()
        if statement:
            execute(statement, fetch=None)


def record_run(
    *,
    user_id: Optional[int],
    query: str,
    answer: str,
    provider: str = "",
    model: str = "",
    skill: str = "",
    confidence: float = 0.50,
    verification_status: str = "unverified",
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    initialize_evolution_store()
    import json
    confidence = max(0.0, min(1.0, float(confidence)))
    row = execute(
        """INSERT INTO intelligence_runs(user_id, query, answer, provider, model, skill, confidence, verification_status, metadata)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb) RETURNING id;""",
        (user_id, str(query), str(answer), str(provider), str(model), str(skill), confidence,
         str(verification_status or "unverified"), json.dumps(metadata or {}, ensure_ascii=False)),
        fetch="one",
    )
    return row[0] if row else None


def record_feedback(
    run_id: int,
    *,
    rating: Optional[int] = None,
    feedback: str = "",
    corrected_answer: str = "",
) -> bool:
    initialize_evolution_store()
    if rating is not None:
        rating = max(1, min(5, int(rating)))
    row = execute(
        """INSERT INTO intelligence_feedback(run_id, rating, feedback, corrected_answer)
        VALUES (%s,%s,%s,%s) RETURNING id;""",
        (int(run_id), rating, str(feedback or "")[:10_000], str(corrected_answer or "")[:100_000]),
        fetch="one",
    )
    return bool(row)


def evaluate_sources(sources: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    items = list(sources or [])
    if not items:
        return {"status": "no_evidence", "confidence": 0.0, "source_count": 0}
    scores: List[float] = []
    for item in items:
        try:
            score = float(item.get("score", 0.0) or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        scores.append(max(0.0, min(1.0, score)))
    confidence = sum(scores) / len(scores)
    status = "verified" if confidence >= 0.75 and len(items) >= 2 else "partially_verified"
    return {"status": status, "confidence": round(confidence, 4), "source_count": len(items)}
