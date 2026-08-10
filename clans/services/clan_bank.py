from core.database import db_manager

async def deposit_to_clan(guild_id: int, user_id: int, clan_id: int, amount: int) -> bool:
    async with db_manager.pool.acquire() as conn:
        async with conn.transaction():
            # Check user balance
            user = await conn.fetchrow(
                "SELECT balance FROM users WHERE guild_id = $1 AND user_id = $2 FOR UPDATE",
                guild_id, user_id
            )
            if not user or user["balance"] < amount:
                return False
            
            # Deduct from user
            await conn.execute(
                "UPDATE users SET balance = balance - $1 WHERE guild_id = $2 AND user_id = $3",
                amount, guild_id, user_id
            )
            
            # Add to clan
            await conn.execute(
                "UPDATE clans SET balance = balance + $1 WHERE clan_id = $2",
                amount, clan_id
            )
            return True

async def withdraw_from_clan(guild_id: int, user_id: int, clan_id: int, amount: int) -> bool:
    async with db_manager.pool.acquire() as conn:
        async with conn.transaction():
            # Check clan balance
            clan = await conn.fetchrow(
                "SELECT balance FROM clans WHERE clan_id = $1 FOR UPDATE",
                clan_id
            )
            if not clan or clan["balance"] < amount:
                return False
            
            # Deduct from clan
            await conn.execute(
                "UPDATE clans SET balance = balance - $1 WHERE clan_id = $2",
                amount, clan_id
            )
            
            # Add to user
            await conn.execute(
                "UPDATE users SET balance = balance + $1 WHERE guild_id = $2 AND user_id = $3",
                amount, guild_id, user_id
            )
            return True
