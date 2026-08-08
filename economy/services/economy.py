import aiosqlite
from ..database import DB_PATH
from ..config import CONFIG

async def get_balance(guild_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance, bank FROM users WHERE guild_id=? AND user_id=?", (guild_id, user_id)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row

        start_balance = int(CONFIG["START_BALANCE"])
        await db.execute(
            """
            INSERT INTO users (guild_id, user_id, balance, bank, total_earned, total_spent, created_at)
            VALUES (?, ?, ?, 0, 0, 0, datetime('now'))
            """,
            (guild_id, user_id, start_balance),
        )
        await db.commit()
        return start_balance, 0

async def add_money(guild_id: int, user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (guild_id, user_id, balance, total_earned) 
            VALUES (?, ?, ?, ?) 
            ON CONFLICT(guild_id, user_id) DO UPDATE SET balance = balance + ?, total_earned = total_earned + ?
        """, (guild_id, user_id, amount, amount, amount, amount))
        await db.commit()

async def remove_money(guild_id: int, user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance - ?, total_spent = total_spent + ? WHERE guild_id=? AND user_id=?", (amount, amount, guild_id, user_id))
        await db.commit()
