from core.database import db_manager
from ..config import CONFIG

async def get_balance(guild_id: int, user_id: int):
    row = await db_manager.fetchrow(
        "SELECT balance, bank FROM users WHERE guild_id=$1 AND user_id=$2",
        guild_id, user_id
    )
    if row:
        return row["balance"], row["bank"]

    start_balance = int(CONFIG["START_BALANCE"])
    await db_manager.execute(
        """
        INSERT INTO users (guild_id, user_id, balance, bank)
        VALUES ($1, $2, $3, 0)
        ON CONFLICT (guild_id, user_id) DO NOTHING
        """,
        guild_id, user_id, start_balance
    )
    return start_balance, 0

async def add_money(guild_id: int, user_id: int, amount: int):
    # Atomic update
    await db_manager.execute("""
        INSERT INTO users (guild_id, user_id, balance) 
        VALUES ($1, $2, $3) 
        ON CONFLICT (guild_id, user_id) DO UPDATE SET balance = users.balance + $3
    """, guild_id, user_id, amount)

async def remove_money(guild_id: int, user_id: int, amount: int):
    # Atomic update with balance check
    await db_manager.execute(
        "UPDATE users SET balance = balance - $1 WHERE guild_id=$2 AND user_id=$3 AND balance >= $1", 
        amount, guild_id, user_id
    )

