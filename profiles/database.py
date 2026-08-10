from core.database import db_manager

class ProfileDatabase:
    def __init__(self): 
        pass

    async def get_profile(self, user_id, guild_id=0):
        row = await db_manager.fetchrow(
            "SELECT messages, voice_seconds as voice, xp, level, balance as coins FROM users WHERE user_id = $1 AND guild_id = $2",
            user_id, guild_id
        )
        if row:
            return dict(row)
        return None

    async def create_profile(self, user_id, guild_id=0):
        await db_manager.execute(
            "INSERT INTO users (user_id, guild_id, messages, voice_seconds, xp, level, balance) VALUES ($1, $2, 0, 0, 0, 1, 0) ON CONFLICT (user_id, guild_id) DO NOTHING",
            user_id, guild_id
        )

    async def update_profile(self, user_id, guild_id=0, messages=None, voice=None, xp=None, level=None, coins=None):
        if messages is not None:
            await db_manager.execute("UPDATE users SET messages = $1 WHERE user_id = $2 AND guild_id = $3", messages, user_id, guild_id)
        if voice is not None:
            await db_manager.execute("UPDATE users SET voice_seconds = $1 WHERE user_id = $2 AND guild_id = $3", voice, user_id, guild_id)
        if xp is not None:
            await db_manager.execute("UPDATE users SET xp = $1 WHERE user_id = $2 AND guild_id = $3", xp, user_id, guild_id)
        if level is not None:
            await db_manager.execute("UPDATE users SET level = $1 WHERE user_id = $2 AND guild_id = $3", level, user_id, guild_id)
        if coins is not None:
            await db_manager.execute("UPDATE users SET balance = $1 WHERE user_id = $2 AND guild_id = $3", coins, user_id, guild_id)

    async def setup(self):
        pass
