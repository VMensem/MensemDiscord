from core.database import db_manager

async def init_db():
    pass

async def create_ticket(guild_id, user_id, channel_id, category_id=None):
    row = await db_manager.fetchrow(
        """
        INSERT INTO tickets (guild_id, user_id, channel_id, category_id, status)
        VALUES ($1, $2, $3, $4, 'open')
        RETURNING ticket_id
        """,
        guild_id, user_id, channel_id, category_id
    )
    return row["ticket_id"] if row else None

async def close_ticket(channel_id):
    await db_manager.execute(
        "UPDATE tickets SET status = 'closed', closed_at = CURRENT_TIMESTAMP WHERE channel_id = $1",
        channel_id
    )
