from core.database import db_manager

class ProfileDatabase:
    async def get_profile(self, user_id, guild_id):
        row = await db_manager.fetchrow(
            "SELECT messages, voice_seconds as voice, xp, level, balance as coins FROM users WHERE user_id = $1 AND guild_id = $2",
            user_id, guild_id
        )
        return dict(row) if row else None

    async def ensure_profile(self, user_id, guild_id):
        await db_manager.execute(
            """
            INSERT INTO users (user_id, guild_id, messages, voice_seconds, xp, level, balance) 
            VALUES ($1, $2, 0, 0, 0, 1, 0) 
            ON CONFLICT (user_id, guild_id) DO NOTHING
            """,
            user_id, guild_id
        )

    async def update_profile(self, user_id, guild_id, messages=None, voice=None, xp=None, level=None, coins=None):
        query = "UPDATE users SET "
        updates = []
        args = []
        
        if messages is not None:
            updates.append(f"messages = ${len(args)+1}")
            args.append(messages)
        if voice is not None:
            updates.append(f"voice_seconds = ${len(args)+1}")
            args.append(voice)
        if xp is not None:
            updates.append(f"xp = ${len(args)+1}")
            args.append(xp)
        if level is not None:
            updates.append(f"level = ${len(args)+1}")
            args.append(level)
        if coins is not None:
            updates.append(f"balance = ${len(args)+1}")
            args.append(coins)
        
        if not updates:
            return

        query += ", ".join(updates) + f" WHERE user_id = ${len(args)+1} AND guild_id = ${len(args)+2}"
        args.extend([user_id, guild_id])
        
        await db_manager.execute(query, *args)
