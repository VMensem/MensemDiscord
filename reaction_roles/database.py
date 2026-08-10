from core.database import db_manager

async def add_reaction_role(guild_id: int, message_id: int, emoji: str, role_id: int):
    await db_manager.execute(
        """
        INSERT INTO reaction_roles (guild_id, message_id, emoji, role_id)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (guild_id, message_id, emoji) DO UPDATE SET role_id = $4
        """,
        guild_id, message_id, emoji, role_id
    )

async def get_role_id(guild_id: int, message_id: int, emoji: str) -> int | None:
    row = await db_manager.fetchrow(
        """
        SELECT role_id FROM reaction_roles
        WHERE guild_id = $1 AND message_id = $2 AND emoji = $3
        """,
        guild_id, message_id, emoji
    )
    return row["role_id"] if row else None
