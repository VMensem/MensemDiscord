from core.database import db_manager

async def init_db():
    pass

async def add_suggestion(guild_id, author_id, channel_id, title, description):
    row = await db_manager.fetchrow(
        """
        INSERT INTO suggestions (guild_id, author_id, channel_id, title, description)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING suggestion_id
        """,
        guild_id, author_id, channel_id, title, description
    )
    return row["suggestion_id"] if row else 0

async def get_suggestion(suggestion_id):
    return await db_manager.fetchrow(
        "SELECT * FROM suggestions WHERE suggestion_id = $1",
        suggestion_id
    )

async def update_suggestion(suggestion_id, **kwargs):
    fields = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
    values = list(kwargs.values())
    await db_manager.execute(
        f"UPDATE suggestions SET {fields} WHERE suggestion_id = $1",
        suggestion_id, *values
    )
