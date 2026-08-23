from core.database import db_manager

async def init_db():
    pass

async def get_config(guild_id: int, key: str):
    row = await db_manager.fetchrow(
        "SELECT value FROM suggestion_config WHERE guild_id = $1 AND key = $2",
        guild_id, key
    )
    return row["value"] if row else None

async def set_config(guild_id: int, key: str, value: int):
    await db_manager.execute(
        """
        INSERT INTO suggestion_config (guild_id, key, value) VALUES ($1, $2, $3)
        ON CONFLICT (guild_id, key) DO UPDATE SET value = $3
        """,
        guild_id, key, value
    )

async def add_suggestion(guild_id: int, author_id: int, channel_id: int, title: str, description: str):
    row = await db_manager.fetchrow(
        """
        INSERT INTO suggestions (guild_id, author_id, channel_id, title, description)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING suggestion_id
        """,
        guild_id, author_id, channel_id, title, description
    )
    return row["suggestion_id"] if row else 0

async def update_suggestion(suggestion_id: int, **kwargs):
    fields = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
    values = list(kwargs.values())
    await db_manager.execute(
        f"UPDATE suggestions SET {fields} WHERE suggestion_id = $1",
        suggestion_id, *values
    )

async def get_suggestion(suggestion_id: int):
    return await db_manager.fetchrow(
        "SELECT * FROM suggestions WHERE suggestion_id = $1",
        suggestion_id
    )

async def get_suggestion_by_message(message_id: int):
    return await db_manager.fetchrow(
        "SELECT * FROM suggestions WHERE message_id = $1",
        message_id
    )

async def get_recent_suggestions(guild_id: int, limit=10):
    return await db_manager.fetch(
        "SELECT * FROM suggestions WHERE guild_id = $1 ORDER BY suggestion_id DESC LIMIT $2",
        guild_id, limit
    )
