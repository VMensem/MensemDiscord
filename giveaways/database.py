from core.database import db_manager

async def get_all_giveaways():
    query = "SELECT * FROM giveaways"
    return await db_manager.fetch(query)


async def create_giveaway(
        message_id: int,
        channel_id: int,
        guild_id: int,
        prize: str,
        winner_count: int,
        conditions: str,
        end_time: str,
        creator: int
):
    query = """
    INSERT INTO giveaways (message_id, channel_id, guild_id, prize, winner_count, conditions, creator_id, end_time)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """
    await db_manager.execute(query, message_id, channel_id, guild_id, prize, winner_count, conditions, creator, end_time)


async def get_giveaway(message_id: int):
    query = "SELECT * FROM giveaways WHERE message_id = $1"
    return await db_manager.fetchrow(query, message_id)


async def add_participant(message_id: int, user_id: int) -> bool:
    query_check = "SELECT 1 FROM giveaway_participants WHERE message_id = $1 AND user_id = $2"
    exists = await db_manager.fetchrow(query_check, message_id, user_id)
    if exists:
        return False
    
    query = """
    INSERT INTO giveaway_participants (message_id, user_id)
    VALUES ($1, $2)
    """
    await db_manager.execute(query, message_id, user_id)
    return True


async def remove_participant(message_id: int, user_id: int):
    query = "DELETE FROM giveaway_participants WHERE message_id = $1 AND user_id = $2"
    await db_manager.execute(query, message_id, user_id)


async def get_participants(message_id: int):
    query = "SELECT user_id FROM giveaway_participants WHERE message_id = $1"
    rows = await db_manager.fetch(query, message_id)
    return [row['user_id'] for row in rows]


async def finish_giveaway(message_id: int):
    query = "UPDATE giveaways SET ended = TRUE WHERE message_id = $1"
    await db_manager.execute(query, message_id)

async def add_winner(message_id: int, user_id: int, position: int):
    query = """
    INSERT INTO giveaway_winners (message_id, user_id, position)
    VALUES ($1, $2, $3)
    """
    await db_manager.execute(query, message_id, user_id, position)

async def get_winners(message_id: int):
    query = "SELECT user_id FROM giveaway_winners WHERE message_id = $1 AND is_active = TRUE"
    rows = await db_manager.fetch(query, message_id)
    return [row['user_id'] for row in rows]

async def deactivate_winner(message_id: int, user_id: int):
    query = "UPDATE giveaway_winners SET is_active = FALSE WHERE message_id = $1 AND user_id = $2"
    await db_manager.execute(query, message_id, user_id)

async def add_reroll_history(message_id: int, old_winner_id: int, new_winner_id: int, performed_by: int):
    query = """
    INSERT INTO giveaway_rerolls (message_id, old_winner_id, new_winner_id, performed_by)
    VALUES ($1, $2, $3, $4)
    """
    await db_manager.execute(query, message_id, old_winner_id, new_winner_id, performed_by)

