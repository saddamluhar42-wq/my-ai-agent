"""Memory intelligence: scoring, consolidation, decay, and safe forgetting."""
from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class MemoryDecision:
    memory_id: int
    score: float
    action: str
    reasons: List[str]


class MemoryIntelligence:
    """Deterministic memory policy; it never deletes high-importance memories silently."""

    def __init__(self, db_path: str = "data/long_term_memory.sqlite3"):
        self.db_path = db_path

    def _db(self):
        return sqlite3.connect(self.db_path)

    @staticmethod
    def _days_since(value: Optional[str]) -> float:
        if not value:
            return 0.0
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0)
        except ValueError:
            return 0.0

    def rank(self, query: str, limit: int = 20) -> List[MemoryDecision]:
        terms = {x.lower() for x in query.split() if len(x) > 1}
        with self._db() as db:
            rows = db.execute("SELECT id,content,importance,created_at,last_used_at FROM memories").fetchall()
        decisions: List[MemoryDecision] = []
        for memory_id, content, importance, created_at, last_used_at in rows:
            words = set(content.lower().split())
            overlap = len(terms & words) / max(1, len(terms))
            age = self._days_since(last_used_at or created_at)
            recency = math.exp(-age / 180.0)
            score = min(1.0, 0.55 * overlap + 0.30 * float(importance) + 0.15 * recency)
            action = "retrieve" if score >= 0.20 else "ignore"
            decisions.append(MemoryDecision(memory_id, score, action, [f"term_overlap={overlap:.2f}", f"importance={float(importance):.2f}", f"recency={recency:.2f}"]))
        return sorted(decisions, key=lambda x: x.score, reverse=True)[:max(1, limit)]

    def consolidate(self, min_importance: float = 0.80) -> int:
        """Mark durable memories by raising importance; no destructive merge is performed."""
        with self._db() as db:
            cur = db.execute("UPDATE memories SET importance = MAX(importance, ?) WHERE importance >= ?", (min_importance, min_importance))
            return cur.rowcount

    def decay_candidates(self, days: int = 365, importance_ceiling: float = 0.30) -> List[int]:
        with self._db() as db:
            rows = db.execute("SELECT id,importance,COALESCE(last_used_at,created_at) FROM memories").fetchall()
        return [rid for rid, imp, ts in rows if float(imp) <= importance_ceiling and self._days_since(ts) >= days]

    def forget(self, memory_ids: List[int], *, explicit_confirmation: bool = False) -> int:
        if not explicit_confirmation or not memory_ids:
            return 0
        placeholders = ",".join("?" for _ in memory_ids)
        with self._db() as db:
            cur = db.execute(f"DELETE FROM memories WHERE id IN ({placeholders}) AND importance < 0.80", memory_ids)
            return cur.rowcount
