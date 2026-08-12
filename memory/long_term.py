"""Persistent long-term memory with relevance and knowledge-graph links."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class MemoryRecord:
    content: str
    category: str = "general"
    importance: float = 0.5
    source: str = "agent"
    tags: List[str] | None = None
    graph_entity: Optional[str] = None
    graph_relation: Optional[str] = None
    graph_target: Optional[str] = None


class LongTermMemory:
    """Durable local memory. Secrets are never inferred or persisted by this class."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or os.getenv("ULTRA_LEGEND_MEMORY_DB", "data/long_term_memory.sqlite3")
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self._init()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _init(self):
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                importance REAL NOT NULL,
                source TEXT NOT NULL,
                tags TEXT NOT NULL,
                graph_entity TEXT,
                graph_relation TEXT,
                graph_target TEXT,
                created_at TEXT NOT NULL,
                last_used_at TEXT
            )""")

    def remember(self, record: MemoryRecord) -> bool:
        content = record.content.strip()
        if not content:
            return False
        fingerprint = hashlib.sha256(content.encode("utf-8")).hexdigest()
        with self._connect() as db:
            try:
                db.execute(
                    """INSERT INTO memories
                    (fingerprint,content,category,importance,source,tags,graph_entity,graph_relation,graph_target,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (fingerprint, content, record.category, max(0.0, min(1.0, record.importance)),
                     record.source, json.dumps(record.tags or [], ensure_ascii=False), record.graph_entity,
                     record.graph_relation, record.graph_target, datetime.now(timezone.utc).isoformat()),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def search(self, query: str, limit: int = 10, category: Optional[str] = None) -> List[Dict[str, Any]]:
        terms = [x.lower() for x in query.split() if len(x) > 1][:12]
        if not terms:
            return []
        clauses = " OR ".join(["lower(content) LIKE ?" for _ in terms])
        params: List[Any] = [f"%{t}%" for t in terms]
        sql = f"SELECT * FROM memories WHERE ({clauses})"
        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY importance DESC, id DESC LIMIT ?"
        params.append(max(1, min(100, limit)))
        with self._connect() as db:
            rows = db.execute(sql, params).fetchall()
        columns = ["id", "fingerprint", "content", "category", "importance", "source", "tags", "graph_entity", "graph_relation", "graph_target", "created_at", "last_used_at"]
        return [dict(zip(columns, row)) for row in rows]

    def graph_context(self, entity: str, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT content, graph_entity, graph_relation, graph_target, importance
                   FROM memories WHERE graph_entity = ? OR graph_target = ?
                   ORDER BY importance DESC, id DESC LIMIT ?""",
                (entity, entity, max(1, min(100, limit))),
            ).fetchall()
        return [{"content": r[0], "entity": r[1], "relation": r[2], "target": r[3], "importance": r[4]} for r in rows]

    def count(self) -> int:
        with self._connect() as db:
            return int(db.execute("SELECT COUNT(*) FROM memories").fetchone()[0])
