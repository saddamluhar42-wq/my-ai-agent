from database.connection import execute, execute_script


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
    CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
    ON messages(conversation_id);
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


def initialize_database():
    execute_script(SCHEMA)


def get_or_create_user(
    external_id,
    display_name="User",
):
    row = execute(
        """
        SELECT id
        FROM users
        WHERE external_id = %s
        LIMIT 1;
        """,
        (external_id,),
        fetch="one",
    )

    if row:
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


def get_or_create_conversation(
    user_id,
    title="New Conversation",
):
    row = execute(
        """
        SELECT id
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


def update_conversation_timestamp(
    conversation_id,
):
    execute(
        """
        UPDATE conversations
        SET updated_at = NOW()
        WHERE id = %s;
        """,
        (conversation_id,),
    )


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
