from core.database import db_manager

async def save_template(guild_id: int, user_id: int, name: str, json_data: str):
    await db_manager.execute(
        """
        INSERT INTO message_templates (guild_id, user_id, name, json_data)
        VALUES ($1, $2, $3, $4)
        """,
        guild_id, user_id, name, json_data
    )

async def get_template(guild_id: int, name: str):
    return await db_manager.fetchrow(
        "SELECT * FROM message_templates WHERE guild_id = $1 AND name = $2",
        guild_id, name
    )
