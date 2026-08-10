from core.database import db_manager
from datetime import datetime

async def create_event(
    guild_id: int,
    creator_id: int,
    title: str,
    description: str,
    start_time: str, # converted from event_date
    duration: str, # Not directly in core schema, keeping it simple for now or adding to description
    max_participants: int,
    reward: str,
    channel_id: int | None,
    message_id: int | None,
) -> int:
    # Adding duration/channel_id/message_id to description for now to fit simple schema or extending schema later
    row = await db_manager.fetchrow(
        """
        INSERT INTO events (
            guild_id,
            creator_id,
            title,
            description,
            start_time,
            max_participants,
            reward,
            state
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, 'draft')
        RETURNING event_id
        """,
        guild_id,
        creator_id,
        title,
        f"{description}\nDuration: {duration}\nChannel: {channel_id}\nMessage: {message_id}",
        start_time,
        max_participants,
        reward
    )
    return row["event_id"] if row else 0

async def add_event_history(event_id: int, action: str, actor_id: int, details: str) -> None:
    # This might need a new table in core/schema.sql
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
    
    total = row[0] or 0
    pending = row[1] or 0
    return int(total), int(pending)
