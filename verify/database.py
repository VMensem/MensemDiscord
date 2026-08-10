from core.database import db_manager

async def init_database() -> None:
    pass

async def get_voice_seconds(guild_id: int, member_id: int) -> int:
    row = await db_manager.fetchrow(
        "SELECT seconds FROM verify_voice_totals WHERE guild_id = $1 AND member_id = $2",
        guild_id, member_id
    )
    return row["seconds"] if row else 0

async def add_voice_seconds(guild_id: int, member_id: int, seconds: int) -> None:
    await db_manager.execute(
        """
        INSERT INTO verify_voice_totals (guild_id, member_id, seconds)
        VALUES ($1, $2, $3)
        ON CONFLICT (guild_id, member_id) DO UPDATE SET seconds = verify_voice_totals.seconds + $3
        """,
        guild_id, member_id, seconds
    )

async def load_stats_db():
    # Placeholder for migration or if needed for legacy compatibility
    return {}, {}, {}, {}, set()

async def save_stats_db(*args):
    # Placeholder for migration or if needed for legacy compatibility
    pass

