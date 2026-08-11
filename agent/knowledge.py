import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from database.connection import execute


KNOWLEDGE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS agent_knowledge (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    category TEXT NOT NULL DEFAULT 'general',
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, category, key)
);

CREATE INDEX IF NOT EXISTS idx_agent_knowledge_user
ON agent_knowledge(user_id);

CREATE INDEX IF NOT EXISTS idx_agent_knowledge_category
ON agent_knowledge(category);

CREATE INDEX IF NOT EXISTS idx_agent_knowledge_key
ON agent_knowledge(key);
"""


def initialize_knowledge_table():
    statements = [
        statement.strip()
        for statement in KNOWLEDGE_TABLE_SQL.split(";")
        if statement.strip()
    ]

    for statement in statements:
        execute(
            statement,
            fetch=None,
        )


def _clean_text(
    value: Any,
    max_length: int = 2000,
) -> str:
    text = str(value or "").strip()

    if len(text) > max_length:
        text = text[:max_length].rstrip()

    return text


def _normalize_key(
    key: str,
) -> str:
    key = _clean_text(
        key,
        max_length=200,
    ).lower()

    key = re.sub(
        r"\s+",
        "_",
        key,
    )

    key = re.sub(
        r"[^a-z0-9_\-]",
        "",
        key,
    )

    return key[:100]


def _clamp_confidence(
    confidence: Any,
) -> float:
    try:
        value = float(
            confidence
        )
    except (
        TypeError,
        ValueError,
    ):
        value = 0.0

    return max(
        0.0,
        min(value, 1.0),
    )


def save_knowledge(
    user_id: Optional[int],
    key: str,
    value: Any,
    category: str = "general",
    source: str = "conversation",
    confidence: float = 1.0,
):
    key = _normalize_key(key)

    if not key:
        return None

    category = _clean_text(
        category or "general",
        max_length=100,
    ) or "general"

    source = _clean_text(
        source or "conversation",
        max_length=200,
    ) or "conversation"

    confidence = _clamp_confidence(
        confidence
    )

    if isinstance(
        value,
        (dict, list),
    ):
        value = json.dumps(
            value,
            ensure_ascii=False,
        )
    else:
        value = _clean_text(
            value,
            max_length=4000,
        )

    if not value:
        return None

    initialize_knowledge_table()

    row = execute(
        """
        INSERT INTO agent_knowledge (
            user_id,
            category,
            key,
            value,
            source,
            confidence,
            created_at,
            updated_at
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            NOW(),
            NOW()
        )
        ON CONFLICT (
            user_id,
            category,
            key
        )
        DO UPDATE SET
            value = EXCLUDED.value,
            source = EXCLUDED.source,
            confidence = EXCLUDED.confidence,
            updated_at = NOW()
        RETURNING id;
        """,
        (
            user_id,
            category,
            key,
            value,
            source,
            confidence,
        ),
        fetch="one",
    )

    return row[0] if row else None


def get_knowledge(
    user_id: Optional[int],
    key: str,
    category: Optional[str] = None,
):
    key = _normalize_key(key)

    if not key:
        return None

    initialize_knowledge_table()

    if category:
        row = execute(
            """
            SELECT
                id,
                category,
                key,
                value,
                source,
                confidence,
                created_at,
                updated_at
            FROM agent_knowledge
            WHERE user_id = %s
              AND category = %s
              AND key = %s
            LIMIT 1;
            """,
            (
                user_id,
                category,
                key,
            ),
            fetch="one",
        )
    else:
        row = execute(
            """
            SELECT
                id,
                category,
                key,
                value,
                source,
                confidence,
                created_at,
                updated_at
            FROM agent_knowledge
            WHERE user_id = %s
              AND key = %s
            ORDER BY updated_at DESC
            LIMIT 1;
            """,
            (
                user_id,
                key,
            ),
            fetch="one",
        )

    if not row:
        return None

    return _row_to_dict(row)


def search_knowledge(
    user_id: Optional[int],
    query: str,
    limit: int = 20,
):
    query = _clean_text(
        query,
        max_length=500,
    )

    if not query:
        return []

    safe_limit = max(
        1,
        min(int(limit), 50),
    )

    initialize_knowledge_table()

    search = f"%{query}%"

    rows = execute(
        f"""
        SELECT
            id,
            category,
            key,
            value,
            source,
            confidence,
            created_at,
            updated_at
        FROM agent_knowledge
        WHERE user_id = %s
          AND (
              key ILIKE %s
              OR value ILIKE %s
              OR category ILIKE %s
          )
        ORDER BY
            confidence DESC,
            updated_at DESC,
            id DESC
        LIMIT {safe_limit};
        """,
        (
            user_id,
            search,
            search,
            search,
        ),
        fetch="all",
    )

    return [
        _row_to_dict(row)
        for row in rows
    ]


def get_all_knowledge(
    user_id: Optional[int],
    limit: int = 100,
):
    safe_limit = max(
        1,
        min(int(limit), 200),
    )

    initialize_knowledge_table()

    rows = execute(
        f"""
        SELECT
            id,
            category,
            key,
            value,
            source,
            confidence,
            created_at,
            updated_at
        FROM agent_knowledge
        WHERE user_id = %s
        ORDER BY
            updated_at DESC,
            id DESC
        LIMIT {safe_limit};
        """,
        (user_id,),
        fetch="all",
    )

    return [
        _row_to_dict(row)
        for row in rows
    ]


def delete_knowledge(
    user_id: Optional[int],
    key: str,
    category: Optional[str] = None,
):
    key = _normalize_key(key)

    if not key:
        return False

    initialize_knowledge_table()

    if category:
        execute(
            """
            DELETE FROM agent_knowledge
            WHERE user_id = %s
              AND category = %s
              AND key = %s;
            """,
            (
                user_id,
                category,
                key,
            ),
        )
    else:
        execute(
            """
            DELETE FROM agent_knowledge
            WHERE user_id = %s
              AND key = %s;
            """,
            (
                user_id,
                key,
            ),
        )

    return True


def build_knowledge_context(
    user_id: Optional[int],
    query: str,
    limit: int = 20,
):
    items = search_knowledge(
        user_id=user_id,
        query=query,
        limit=limit,
    )

    if not items:
        return "No persistent knowledge found."

    lines = [
        "PERSISTENT AGENT KNOWLEDGE:"
    ]

    for item in items:
        lines.append(
            (
                f"- [{item['category']}] "
                f"{item['key']}: "
                f"{item['value']} "
                f"(confidence: "
                f"{item['confidence']:.2f})"
            )
        )

    return "\n".join(lines)


# ============================================================
# LEARNING DETECTION
# ============================================================

_EXPLICIT_MEMORY_PATTERNS = (
    "remember this",
    "remember that",
    "remember it",
    "save this",
    "save that",
    "save it",
    "keep this in memory",
    "keep this in mind",
    "don't forget this",
    "do not forget this",
    "yaad rakhna",
    "ye yaad rakhna",
    "isko yaad rakhna",
    "ise yaad rakhna",
    "save karna",
    "memory me save",
    "memory mein save",
)

_CORRECTION_PATTERNS = (
    "actually",
    "correct this",
    "correction",
    "that's wrong",
    "that is wrong",
    "galat hai",
    "sahi ye hai",
    "correct ye hai",
    "nahi,",
    "नहीं",
    "गलत",
    "सही",
)

_PREFERENCE_PATTERNS = (
    "i prefer",
    "i like",
    "i want",
    "my preference",
    "i always want",
    "mujhe pasand",
    "mujhe chahiye",
    "meri preference",
    "main chahta",
    "main chahti",
)


def _contains_pattern(
    text: str,
    patterns,
) -> bool:
    text = text.lower()

    return any(
        pattern in text
        for pattern in patterns
    )


def _extract_after_marker(
    query: str,
    markers,
) -> str:
    query_lower = query.lower()

    for marker in markers:
        index = query_lower.find(
            marker
        )

        if index >= 0:
            value = query[
                index + len(marker):
            ].strip(
                " :,-.!?"
            )

            if value:
                return value

    return ""


def _explicit_memory_candidate(
    query: str,
) -> Optional[Dict[str, Any]]:

    if not _contains_pattern(
        query,
        _EXPLICIT_MEMORY_PATTERNS,
    ):
        return None

    value = _extract_after_marker(
        query,
        _EXPLICIT_MEMORY_PATTERNS,
    )

    if not value:
        value = query

    value = _clean_text(
        value,
        max_length=1000,
    )

    return {
        "category": "user_preference",
        "key": "explicit_memory",
        "value": value,
        "source": "explicit_user_request",
        "confidence": 0.98,
    }


def _preference_candidate(
    query: str,
) -> Optional[Dict[str, Any]]:

    if not _contains_pattern(
        query,
        _PREFERENCE_PATTERNS,
    ):
        return None

    value = _clean_text(
        query,
        max_length=1000,
    )

    return {
        "category": "user_preference",
        "key": "preference",
        "value": value,
        "source": "conversation",
        "confidence": 0.90,
    }


def _correction_candidate(
    query: str,
) -> Optional[Dict[str, Any]]:

    if not _contains_pattern(
        query,
        _CORRECTION_PATTERNS,
    ):
        return None

    value = _clean_text(
        query,
        max_length=1000,
    )

    return {
        "category": "user_correction",
        "key": "latest_correction",
        "value": value,
        "source": "user_feedback",
        "confidence": 0.95,
    }


def extract_learning_candidates(
    query: str,
    answer: str,
) -> List[Dict[str, Any]]:
    """
    Extract conservative learning candidates.

    Explicit memory requests and direct user
    preferences/corrections receive high confidence.

    Ordinary questions are NOT automatically
    converted into permanent user knowledge.
    """

    query = _clean_text(
        query,
        max_length=2000,
    )

    answer = _clean_text(
        answer,
        max_length=4000,
    )

    if not query or not answer:
        return []

    candidates = []

    explicit = _explicit_memory_candidate(
        query
    )

    if explicit:
        candidates.append(
            explicit
        )

    correction = _correction_candidate(
        query
    )

    if correction:
        candidates.append(
            correction
        )

    preference = _preference_candidate(
        query
    )

    if preference:
        candidates.append(
            preference
        )

    return _deduplicate_candidates(
        candidates
    )


def _deduplicate_candidates(
    candidates: List[Dict[str, Any]],
):
    unique = []
    seen = set()

    for candidate in candidates:

        key = (
            candidate.get("category"),
            candidate.get("key"),
            candidate.get("value"),
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(candidate)

    return unique


def evaluate_learning_candidate(
    candidate: Dict[str, Any],
    minimum_confidence: float = 0.70,
) -> bool:

    if not candidate:
        return False

    key = _clean_text(
        candidate.get("key"),
        max_length=100,
    )

    value = _clean_text(
        candidate.get("value"),
        max_length=4000,
    )

    confidence = _clamp_confidence(
        candidate.get(
            "confidence",
            0.0,
        )
    )

    return bool(
        key
        and value
        and confidence >= minimum_confidence
    )


def learning_health():
    """
    Return a simple health report for the
    persistent learning layer.
    """

    initialize_knowledge_table()

    row = execute(
        """
        SELECT
            COUNT(*),
            COUNT(DISTINCT user_id),
            COUNT(*) FILTER (
                WHERE category = 'user_preference'
            ),
            COUNT(*) FILTER (
                WHERE category = 'user_correction'
            ),
            MAX(updated_at)
        FROM agent_knowledge;
        """,
        fetch="one",
    )

    if not row:
        return {
            "records": 0,
            "users": 0,
            "preferences": 0,
            "corrections": 0,
            "last_update": None,
            "status": "ready",
        }

    last_update = row[4]

    if isinstance(
        last_update,
        datetime,
    ):
        last_update = (
            last_update.astimezone(
                timezone.utc
            ).isoformat()
        )

    return {
        "records": int(row[0] or 0),
        "users": int(row[1] or 0),
        "preferences": int(row[2] or 0),
        "corrections": int(row[3] or 0),
        "last_update": last_update,
        "status": "ready",
    }


def knowledge_health():
    """
    Backward-compatible alias.
    """

    return learning_health()


def _row_to_dict(row):
    return {
        "id": row[0],
        "category": row[1],
        "key": row[2],
        "value": row[3],
        "source": row[4],
        "confidence": float(
            row[5] or 0.0
        ),
        "created_at": row[6],
        "updated_at": row[7],
    }
