from database.connection import execute, execute_script


# ============================================================
# DATABASE SCHEMA
# ============================================================

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id BIGSERIAL PRIMARY KEY,
        external_id TEXT UNIQUE NOT NULL,
        display_name TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS conversations (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL
            REFERENCES users(id)
            ON DELETE CASCADE,
        title TEXT NOT NULL DEFAULT 'New Conversation',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS messages (
        id BIGSERIAL PRIMARY KEY,
        conversation_id BIGINT NOT NULL
            REFERENCES conversations(id)
            ON DELETE CASCADE,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        provider TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS agent_runs (
        id BIGSERIAL PRIMARY KEY,
        conversation_id BIGINT NOT NULL
            REFERENCES conversations(id)
            ON DELETE CASCADE,
        message_id BIGINT
            REFERENCES messages(id)
            ON DELETE SET NULL,
        provider TEXT,
        model TEXT,
        status TEXT NOT NULL,
        error_message TEXT,
        started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        completed_at TIMESTAMPTZ,
        metadata JSONB
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS user_settings (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL
            REFERENCES users(id)
            ON DELETE CASCADE,
        setting_key TEXT NOT NULL,
        setting_value TEXT,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(user_id, setting_key)
    );
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_conversations_user_id
    ON conversations(user_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
    ON conversations(updated_at DESC);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
    ON messages(conversation_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_messages_created_at
    ON messages(created_at);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_agent_runs_conversation_id
    ON agent_runs(conversation_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_user_settings_user_id
    ON user_settings(user_id);
    """,
]


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():
    execute_script(SCHEMA)


# ============================================================
# USERS
# ============================================================

def get_or_create_user(
    external_id,
    display_name="User",
):
    row = execute(
        """
        SELECT
            id
        FROM users
        WHERE external_id = %s
        LIMIT 1;
        """,
        (external_id,),
        fetch="one",
    )

    if row:
        execute(
            """
            UPDATE users
            SET
                display_name = %s,
                updated_at = NOW()
            WHERE id = %s;
            """,
            (
                display_name,
                row[0],
            ),
        )

        return row[0]

    row = execute(
        """
        INSERT INTO users (
            external_id,
            display_name
        )
        VALUES (%s, %s)
        RETURNING id;
        """,
        (
            external_id,
            display_name,
        ),
        fetch="one",
    )

    return row[0]


# ============================================================
# CONVERSATIONS
# ============================================================

def get_or_create_conversation(
    user_id,
    title="New Conversation",
):
    row = execute(
        """
        SELECT
            id
        FROM conversations
        WHERE user_id = %s
        ORDER BY updated_at DESC, id DESC
        LIMIT 1;
        """,
        (user_id,),
        fetch="one",
    )

    if row:
        return row[0]

    row = execute(
        """
        INSERT INTO conversations (
            user_id,
            title
        )
        VALUES (%s, %s)
        RETURNING id;
        """,
        (
            user_id,
            title,
        ),
        fetch="one",
    )

    return row[0]


def create_conversation(
    user_id,
    title="New Conversation",
):
    row = execute(
        """
        INSERT INTO conversations (
            user_id,
            title
        )
        VALUES (%s, %s)
        RETURNING id;
        """,
        (
            user_id,
            title,
        ),
        fetch="one",
    )

    return row[0]


def get_conversation(
    conversation_id,
):
    if not conversation_id:
        return None

    row = execute(
        """
        SELECT
            id,
            user_id,
            title,
            created_at,
            updated_at
        FROM conversations
        WHERE id = %s
        LIMIT 1;
        """,
        (conversation_id,),
        fetch="one",
    )

    if not row:
        return None

    return {
        "id": row[0],
        "user_id": row[1],
        "title": row[2],
        "created_at": row[3],
        "updated_at": row[4],
    }


def get_recent_conversations(
    user_id,
    limit=30,
):
    if not user_id:
        return []

    safe_limit = max(
        1,
        min(int(limit), 100),
    )

    rows = execute(
        f"""
        SELECT
            c.id,
            c.user_id,
            c.title,
            c.created_at,
            c.updated_at,
            COALESCE(
                (
                    SELECT m.content
                    FROM messages m
                    WHERE m.conversation_id = c.id
                      AND m.role = 'user'
                    ORDER BY m.created_at ASC, m.id ASC
                    LIMIT 1
                ),
                c.title
            ) AS first_message,
            (
                SELECT COUNT(*)
                FROM messages m2
                WHERE m2.conversation_id = c.id
            ) AS message_count
        FROM conversations c
        WHERE c.user_id = %s
        ORDER BY c.updated_at DESC, c.id DESC
        LIMIT {safe_limit};
        """,
        (user_id,),
        fetch="all",
    )

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "title": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "first_message": row[5],
            "message_count": row[6],
        }
        for row in rows
    ]


def update_conversation_title(
    conversation_id,
    title,
):
    if not conversation_id:
        return

    clean_title = str(
        title or "New Conversation"
    ).strip()

    if not clean_title:
        clean_title = "New Conversation"

    execute(
        """
        UPDATE conversations
        SET
            title = %s,
            updated_at = NOW()
        WHERE id = %s;
        """,
        (
            clean_title,
            conversation_id,
        ),
    )


def update_conversation_timestamp(
    conversation_id,
):
    if not conversation_id:
        return

    execute(
        """
        UPDATE conversations
        SET updated_at = NOW()
        WHERE id = %s;
        """,
        (conversation_id,),
    )


# ============================================================
# MESSAGES
# ============================================================

def create_message(
    conversation_id,
    role,
    content,
    provider=None,
):
    row = execute(
        """
        INSERT INTO messages (
            conversation_id,
            role,
            content,
            provider
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id;
        """,
        (
            conversation_id,
            role,
            content,
            provider,
        ),
        fetch="one",
    )

    update_conversation_timestamp(
        conversation_id
    )

    return row[0]


def get_messages(
    conversation_id,
    limit=50,
):
    if not conversation_id:
        return []

    safe_limit = max(
        1,
        min(int(limit), 100),
    )

    return execute(
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


# ============================================================
# AGENT RUNS
# ============================================================

def create_agent_run(
    conversation_id,
    provider=None,
    model=None,
):
    row = execute(
        """
        INSERT INTO agent_runs (
            conversation_id,
            provider,
            model,
            status
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id;
        """,
        (
            conversation_id,
            provider,
            model,
            "running",
        ),
        fetch="one",
    )

    return row[0]


def finish_agent_run(
    run_id,
    status,
    message_id=None,
    error_message=None,
):
    execute(
        """
        UPDATE agent_runs
        SET
            status = %s,
            message_id = %s,
            error_message = %s,
            completed_at = NOW()
        WHERE id = %s;
        """,
        (
            status,
            message_id,
            error_message,
            run_id,
        ),
    )
