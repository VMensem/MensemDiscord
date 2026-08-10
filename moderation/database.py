from core.database import db_manager

async def add_case(guild_id, user_id, mod_id, type, reason):
    row = await db_manager.fetchrow(
        "INSERT INTO moderation_cases (guild_id, user_id, mod_id, type, reason) VALUES ($1, $2, $3, $4, $5) RETURNING case_id",
        guild_id, user_id, mod_id, type, reason
    )
    return row["case_id"] if row else 0
