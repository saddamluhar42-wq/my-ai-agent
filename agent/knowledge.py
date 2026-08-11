import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from database.connection import execute


# ============================================================
# DATABASE SCHEMA
# ============================================================

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


# ============================================================
# INITIALIZATION
# ============================================================

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


# ============================================================
# TEXT HELPERS
# ============================================================

def _clean_text(
    value: Any,
    max_length: int = 2000,
) -> str:

    text = str(
        value or ""
    ).strip()

    if len(text) > max_length:

        text = (
            text[
                :max_length
            ]
            .rstrip()
        )

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
        min(
            value,
            1.0,
        ),
    )


def _stable_key(
    text: str,
    prefix: str,
) -> str:

    digest = hashlib.sha1(
        text.encode(
            "utf-8"
        )
    ).hexdigest()[:16]

    return (
        f"{prefix}_{digest}"
    )


# ============================================================
# SAVE KNOWLEDGE
# ============================================================

def save_knowledge(
    user_id: Optional[int],
    key: str,
    value: Any,
    category: str = "general",
    source: str = "conversation",
    confidence: float = 1.0,
):

    key = _normalize_key(
        key
    )

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

    return (
        row[0]
        if row
        else None
    )


# ============================================================
# GET SINGLE KNOWLEDGE
# ============================================================

def get_knowledge(
    user_id: Optional[int],
    key: str,
    category: Optional[str] = None,
):

    key = _normalize_key(
        key
    )

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

    return _row_to_dict(
        row
    )


# ============================================================
# SEARCH RELEVANT KNOWLEDGE
# ============================================================

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
        min(
            int(limit),
            50,
        ),
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


# ============================================================
# GET ALL KNOWLEDGE
# ============================================================

def get_all_knowledge(
    user_id: Optional[int],
    limit: int = 100,
):

    safe_limit = max(
        1,
        min(
            int(limit),
            200,
        ),
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


# ============================================================
# GET PERMANENT USER PREFERENCES
# ============================================================

def get_user_preferences(
    user_id: Optional[int],
    limit: int = 50,
):

    safe_limit = max(
        1,
        min(
            int(limit),
            100,
        ),
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
          AND category IN (
              'user_preference',
              'language_preference',
              'response_style',
              'project_preference',
              'important_instruction',
              'user_correction'
          )
        ORDER BY
            confidence DESC,
            updated_at DESC,
            id DESC
        LIMIT {safe_limit};
        """,
        (
            user_id,
        ),
        fetch="all",
    )

    return [
        _row_to_dict(row)
        for row in rows
    ]


# ============================================================
# DELETE KNOWLEDGE
# ============================================================

def delete_knowledge(
    user_id: Optional[int],
    key: str,
    category: Optional[str] = None,
):

    key = _normalize_key(
        key
    )

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


# ============================================================
# BUILD KNOWLEDGE CONTEXT
# ============================================================

def build_knowledge_context(
    user_id: Optional[int],
    query: str,
    limit: int = 20,
):

    # --------------------------------------------------------
    # IMPORTANT:
    # Always load permanent user preferences.
    # --------------------------------------------------------

    preferences = get_user_preferences(
        user_id=user_id,
        limit=50,
    )

    # --------------------------------------------------------
    # Also load query-specific knowledge.
    # --------------------------------------------------------

    relevant = search_knowledge(
        user_id=user_id,
        query=query,
        limit=limit,
    )

    combined = []

    seen_ids = set()

    for item in (
        preferences + relevant
    ):

        item_id = item.get(
            "id"
        )

        if item_id in seen_ids:
            continue

        seen_ids.add(
            item_id
        )

        combined.append(
            item
        )

    if not combined:

        return (
            "No persistent knowledge "
            "found."
        )

    # --------------------------------------------------------
    # Sort important preferences first.
    # --------------------------------------------------------

    category_priority = {
        "language_preference": 1,
        "important_instruction": 2,
        "user_preference": 3,
        "response_style": 4,
        "project_preference": 5,
        "user_correction": 6,
    }

    combined.sort(
        key=lambda item: (
            category_priority.get(
                item.get(
                    "category",
                    "general",
                ),
                99,
            ),
            -float(
                item.get(
                    "confidence",
                    0.0,
                )
            ),
        )
    )

    lines = [
        "PERSISTENT USER KNOWLEDGE:",
        "",
        (
            "IMPORTANT: Apply relevant "
            "user preferences and instructions "
            "to the current response."
        ),
    ]

    for item in combined:

        lines.append(
            (
                f"- [{item['category']}] "
                f"{item['key']}: "
                f"{item['value']} "
                f"(confidence: "
                f"{item['confidence']:.2f})"
            )
        )

    return "\n".join(
        lines
    )


# ============================================================
# LEARNING DETECTION
# ============================================================

_EXPLICIT_MEMORY_PATTERNS = (
    "remember this",
    "remember that",
    "remember it",
    "remember",
    "save this",
    "save that",
    "save it",
    "keep this in memory",
    "keep this in mind",
    "don't forget this",
    "do not forget this",
    "yaad rakhna",
    "ye yaad rakhna",
    "yeh yaad rakhna",
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


# ============================================================
# LANGUAGE PREFERENCE DETECTION
# ============================================================

_HINDI_LANGUAGE_PATTERNS = (
    "hindi me jawab",
    "hindi mein jawab",
    "hindi me answer",
    "hindi mein answer",
    "hindi me reply",
    "hindi mein reply",
    "jawab hindi me",
    "jawab hindi mein",
    "answer hindi me",
    "answer hindi mein",
    "reply hindi me",
    "reply hindi mein",
    "हिंदी में जवाब",
    "हिंदी में उत्तर",
    "हिंदी में बताना",
    "हिंदी में बताओ",
)


_ENGLISH_LANGUAGE_PATTERNS = (
    "answer in english",
    "reply in english",
    "respond in english",
    "english me jawab",
    "english mein jawab",
    "english me answer",
    "english mein answer",
    "अंग्रेजी में जवाब",
    "अंग्रेज़ी में जवाब",
)


def _contains_pattern(
    text: str,
    patterns,
) -> bool:

    text = text.lower()

    return any(
        pattern.lower() in text
        for pattern in patterns
    )


def _extract_after_marker(
    query: str,
    markers,
) -> str:

    query_lower = query.lower()

    for marker in markers:

        index = query_lower.find(
            marker.lower()
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


# ============================================================
# LANGUAGE CANDIDATE
# ============================================================

def _language_candidate(
    query: str,
) -> Optional[Dict[str, Any]]:

    if _contains_pattern(
        query,
        _HINDI_LANGUAGE_PATTERNS,
    ):

        return {
            "category": "language_preference",
            "key": "response_language",
            "value": "Hindi",
            "source": "explicit_user_request",
            "confidence": 1.0,
        }

    if _contains_pattern(
        query,
        _ENGLISH_LANGUAGE_PATTERNS,
    ):

        return {
            "category": "language_preference",
            "key": "response_language",
            "value": "English",
            "source": "explicit_user_request",
            "confidence": 1.0,
        }

    return None


# ============================================================
# EXPLICIT MEMORY CANDIDATE
# ============================================================

def _explicit_memory_candidate(
    query: str,
) -> Optional[Dict[str, Any]]:

    if not _contains_pattern(
        query,
        _EXPLICIT_MEMORY_PATTERNS,
    ):
        return None

    # --------------------------------------------------------
    # If this is specifically a language preference,
    # language_candidate handles it with a stable key.
    # --------------------------------------------------------

    if _language_candidate(
        query
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
        "category": "important_instruction",
        "key": _stable_key(
            value,
            "instruction",
        ),
        "value": value,
        "source": "explicit_user_request",
        "confidence": 0.98,
    }


# ============================================================
# PREFERENCE CANDIDATE
# ============================================================

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
        "key": _stable_key(
            value,
            "preference",
        ),
        "value": value,
        "source": "conversation",
        "confidence": 0.90,
    }


# ============================================================
# CORRECTION CANDIDATE
# ============================================================

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


# ============================================================
# LEARNING EXTRACTION
# ============================================================

def extract_learning_candidates(
    query: str,
    answer: str,
) -> List[Dict[str, Any]]:
    """
    Extract conservative learning candidates.

    Permanent preferences are only created when
    the user's message clearly indicates a preference,
    instruction, correction, or explicit memory request.

    Normal questions are NOT permanently memorized.
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

    # --------------------------------------------------------
    # Highest priority: language preference
    # --------------------------------------------------------

    language = _language_candidate(
        query
    )

    if language:

        candidates.append(
            language
        )

    # --------------------------------------------------------
    # Explicit memory
    # --------------------------------------------------------

    explicit = (
        _explicit_memory_candidate(
            query
        )
    )

    if explicit:

        candidates.append(
            explicit
        )

    # --------------------------------------------------------
    # User corrections
    # --------------------------------------------------------

    correction = (
        _correction_candidate(
            query
        )
    )

    if correction:

        candidates.append(
            correction
        )

    # --------------------------------------------------------
    # General preferences
    # --------------------------------------------------------

    preference = (
        _preference_candidate(
            query
        )
    )

    if preference:

        candidates.append(
            preference
        )

    return _deduplicate_candidates(
        candidates
    )


# ============================================================
# DEDUPLICATION
# ============================================================

def _deduplicate_candidates(
    candidates: List[Dict[str, Any]],
):

    unique = []

    seen = set()

    for candidate in candidates:

        key = (
            candidate.get(
                "category"
            ),
            candidate.get(
                "key"
            ),
            candidate.get(
                "value"
            ),
        )

        if key in seen:

            continue

        seen.add(
            key
        )

        unique.append(
            candidate
        )

    return unique


# ============================================================
# CANDIDATE VALIDATION
# ============================================================

def evaluate_learning_candidate(
    candidate: Dict[str, Any],
    minimum_confidence: float = 0.70,
) -> bool:

    if not candidate:

        return False

    key = _clean_text(
        candidate.get(
            "key"
        ),
        max_length=100,
    )

    value = _clean_text(
        candidate.get(
            "value"
        ),
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
        and confidence
        >= minimum_confidence
    )


# ============================================================
# LEARNING HEALTH
# ============================================================

def learning_health():

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
                WHERE category = 'language_preference'
            ),
            COUNT(*) FILTER (
                WHERE category = 'user_correction'
            ),
            COUNT(*) FILTER (
                WHERE category = 'important_instruction'
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
            "language_preferences": 0,
            "corrections": 0,
            "instructions": 0,
            "last_update": None,
            "status": "ready",
        }

    last_update = row[6]

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
        "records": int(
            row[0] or 0
        ),
        "users": int(
            row[1] or 0
        ),
        "preferences": int(
            row[2] or 0
        ),
        "language_preferences": int(
            row[3] or 0
        ),
        "corrections": int(
            row[4] or 0
        ),
        "instructions": int(
            row[5] or 0
        ),
        "last_update": last_update,
        "status": "ready",
    }


def knowledge_health():

    return learning_health()


# ============================================================
# ROW CONVERSION
# ============================================================

def _row_to_dict(
    row,
):

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
