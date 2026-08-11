import json
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
    """
    Create the persistent agent knowledge table.
    """

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


def save_knowledge(
    user_id: Optional[int],
    key: str,
    value: Any,
    category: str = "general",
    source: str = "conversation",
    confidence: float = 1.0,
):
    """
    Save or update persistent knowledge.

    The agent should only store useful, stable information.
    """

    if not key or not str(key).strip():
        return None

    key = str(key).strip()
    category = str(category or "general").strip()
    source = str(source or "conversation").strip()

    confidence = max(
        0.0,
        min(float(confidence), 1.0),
    )

    if isinstance(value, (dict, list)):
        value = json.dumps(
            value,
            ensure_ascii=False,
        )
    else:
        value = str(value)

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
    """
    Retrieve one stored knowledge item.
    """

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
    """
    Search persistent knowledge using PostgreSQL text matching.
    """

    if not query or not query.strip():
        return []

    safe_limit = max(
        1,
        min(int(limit), 50),
    )

    initialize_knowledge_table()

    search = f"%{query.strip()}%"

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
    """
    Return recent persistent knowledge.
    """

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
    """
    Delete stored knowledge.
    """

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
    """
    Convert relevant persistent knowledge into
    prompt-ready context.
    """

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


def extract_learning_candidates(
    query: str,
    answer: str,
) -> List[Dict[str, Any]]:
    """
    Return candidate information that may be useful
    for future learning.

    This function intentionally does NOT automatically
    write everything into permanent memory.

    The next evolution layer will decide what is safe,
    stable, and useful enough to persist.
    """

    query = str(query or "").strip()
    answer = str(answer or "").strip()

    if not query or not answer:
        return []

    candidates = []

    if len(query) >= 10:

        candidates.append(
            {
                "category": "interaction",
                "key": "recent_topic",
                "value": query[:500],
                "source": "conversation",
                "confidence": 0.50,
            }
        )

    return candidates


def _row_to_dict(row):
    return {
        "id": row[0],
        "category": row[1],
        "key": row[2],
        "value": row[3],
        "source": row[4],
        "confidence": float(row[5] or 0.0),
        "created_at": row[6],
        "updated_at": row[7],
    }


def knowledge_health():
    """
    Basic health information for the knowledge layer.
    """

    initialize_knowledge_table()

    row = execute(
        """
        SELECT
            COUNT(*),
            COUNT(DISTINCT user_id),
            MAX(updated_at)
        FROM agent_knowledge;
        """,
        fetch="one",
    )

    if not row:
        return {
            "records": 0,
            "users": 0,
            "last_update": None,
            "status": "ready",
        }

    last_update = row[2]

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
        "last_update": last_update,
        "status": "ready",
    }
