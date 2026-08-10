from core.database import db_manager

async def init_db():
    pass

async def create_event(
    guild_id: int,
    creator_id: int,
    title: str,
    description: str,
    start_time: str,
    duration: str,
    max_participants: int,
    reward: str,
    channel_id: int | None,
    message_id: int | None,
) -> int:
    row = await db_manager.fetchrow(
        """
        INSERT INTO events (
            guild_id, creator_id, title, description, start_time, max_participants, reward, state
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, 'draft')
        RETURNING event_id
        """,
        guild_id, creator_id, title, description, start_time, max_participants, reward
    )
    return row["event_id"] if row else 0

async def add_event_history(event_id: int, action: str, actor_id: int, details: str) -> None:
    pass

async def count_events(guild_id: int | None = None) -> tuple[int, int]:
    if guild_id is not None:
        row = await db_manager.fetchrow(
            "SELECT COUNT(*), SUM(CASE WHEN state = 'draft' THEN 1 ELSE 0 END) FROM events WHERE guild_id = $1",
            guild_id
        )
    else:
        row = await db_manager.fetchrow(
            "SELECT COUNT(*), SUM(CASE WHEN state = 'draft' THEN 1 ELSE 0 END) FROM events"
        )
    return (row[0] or 0, row[1] or 0)
