from core.database import db_manager
import datetime

async def get_relationship(guild_id: int, user_id: int):
    return await db_manager.fetchrow(
        "SELECT * FROM love_relationships WHERE guild_id = $1 AND (user1_id = $2 OR user2_id = $2) AND status = 'active'",
        guild_id, user_id
    )

async def create_proposal(guild_id: int, from_user_id: int, to_user_id: int, expires_at: datetime.datetime) -> int:
    await db_manager.execute(
        "INSERT INTO love_proposals (guild_id, from_user_id, to_user_id, expires_at) VALUES ($1, $2, $3, $4)",
        guild_id, from_user_id, to_user_id, expires_at
    )
    # Get last insert ID
    row = await db_manager.fetchrow("SELECT LAST_INSERT_ID() as id")
    return row["id"]

async def get_pending_proposal(guild_id: int, from_user_id: int, to_user_id: int):
    return await db_manager.fetchrow(
        "SELECT * FROM love_proposals WHERE guild_id = $1 AND from_user_id = $2 AND to_user_id = $3 AND status = 'pending' AND expires_at > $4",
        guild_id, from_user_id, to_user_id, datetime.datetime.now(datetime.timezone.utc)
    )

async def get_pending_proposal_by_id(proposal_id: int):
    return await db_manager.fetchrow("SELECT * FROM love_proposals WHERE proposal_id = $1 AND status = 'pending'", proposal_id)

async def accept_proposal(proposal_id: int, guild_id: int, user1_id: int, user2_id: int):
    async with db_manager.transaction():
        await db_manager.execute("UPDATE love_proposals SET status = 'accepted' WHERE proposal_id = $1", proposal_id)
        await db_manager.execute(
            "INSERT INTO love_relationships (guild_id, user1_id, user2_id) VALUES ($1, $2, $3)",
            guild_id, user1_id, user2_id
        )

async def reject_proposal(proposal_id: int):
    await db_manager.execute("UPDATE love_proposals SET status = 'rejected' WHERE proposal_id = $1", proposal_id)

async def delete_relationship(relationship_id: int):
    async with db_manager.transaction():
        await db_manager.execute("DELETE FROM love_rooms WHERE relationship_id = $1", relationship_id)
        await db_manager.execute("DELETE FROM love_relationships WHERE relationship_id = $1", relationship_id)

async def get_love_room(relationship_id: int):
    return await db_manager.fetchrow("SELECT * FROM love_rooms WHERE relationship_id = $1", relationship_id)

async def add_love_room(guild_id: int, relationship_id: int, channel_id: int):
    await db_manager.execute(
        "INSERT INTO love_rooms (guild_id, relationship_id, channel_id) VALUES ($1, $2, $3)",
        guild_id, relationship_id, channel_id
    )

async def delete_love_room(channel_id: int):
    await db_manager.execute("DELETE FROM love_rooms WHERE channel_id = $1", channel_id)
