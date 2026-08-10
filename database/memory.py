from database.connection import execute
from database.models import create_message


def load_conversation(
    conversation_id,
    limit=50,
):
    if not conversation_id:
        return []

    safe_limit = max(
        1,
        min(int(limit), 100),
    )

    rows = execute(
        f"""
        SELECT
            id,
            role,
            content,
            provider,
            created_at
        FROM messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC, id ASC
        LIMIT {safe_limit};
        """,
        (conversation_id,),
        fetch="all",
    )

    return [
        {
            "id": row[0],
            "role": row[1],
            "content": row[2],
            "provider": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]


def save_user_message(
    conversation_id,
    content,
):
    return create_message(
        conversation_id=conversation_id,
        role="user",
        content=content,
    )


def save_assistant_message(
    conversation_id,
    content,
    provider=None,
):
    return create_message(
        conversation_id=conversation_id,
        role="assistant",
        content=content,
        provider=provider,
    )


def search_memory(
    conversation_id,
    query,
    limit=30,
):
    if not conversation_id:
        return []

    if not query or not query.strip():
        return []

    safe_limit = max(
        1,
        min(int(limit), 50),
    )

    rows = execute(
        f"""
        SELECT
            id,
            role,
            content,
            provider,
            created_at
        FROM messages
        WHERE conversation_id = %s
          AND content ILIKE %s
        ORDER BY created_at DESC, id DESC
        LIMIT {safe_limit};
        """,
        (
            conversation_id,
            f"%{query.strip()}%",
        ),
        fetch="all",
    )

    return [
        {
            "id": row[0],
            "role": row[1],
            "content": row[2],
            "provider": row[3],
            "created_at": row[4],
        }
        for row in reversed(rows)
    ]


def get_recent_messages(
    conversation_id,
    limit=20,
):
    return load_conversation(
        conversation_id,
        limit=limit,
    )


def format_memory_for_prompt(
    messages,
):
    if not messages:
        return "No previous memory available."

    formatted = []

    for message in messages:
        role = message.get(
            "role",
            "unknown",
        ).upper()

        content = message.get(
            "content",
            "",
        )

        formatted.append(
            f"{role}: {content}"
        )

    return "\n\n".join(formatted)


def build_memory_context(
    conversation_id,
    current_query,
    recent_limit=20,
    search_limit=10,
):
    recent = get_recent_messages(
        conversation_id,
        limit=recent_limit,
    )

    relevant = search_memory(
        conversation_id,
        current_query,
        limit=search_limit,
    )

    combined = []
    seen_ids = set()

    for message in recent + relevant:
        message_id = message.get("id")

        if message_id in seen_ids:
            continue

        seen_ids.add(message_id)
        combined.append(message)

    return format_memory_for_prompt(
        combined
    )
