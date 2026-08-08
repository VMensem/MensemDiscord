import aiosqlite
import os

class ProfileDatabase:
    def __init__(self, db_path="profiles/data/profiles.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def get_profile(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT messages, voice, xp, level, coins FROM profiles WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "messages": row[0],
                        "voice": row[1],
                        "xp": row[2],
                        "level": row[3],
                        "coins": row[4]
                    }
                return None

    async def create_profile(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO profiles (user_id, messages, voice, xp, level, coins) VALUES (?, 0, 0, 0, 1, 0)",
                (user_id,)
            )
            await db.commit()

    async def update_profile(self, user_id, messages=None, voice=None, xp=None, level=None, coins=None):
        async with aiosqlite.connect(self.db_path) as db:
            if messages is not None:
                await db.execute("UPDATE profiles SET messages = ? WHERE user_id = ?", (messages, user_id))
            if voice is not None:
                await db.execute("UPDATE profiles SET voice = ? WHERE user_id = ?", (voice, user_id))
            if xp is not None:
                await db.execute("UPDATE profiles SET xp = ? WHERE user_id = ?", (xp, user_id))
            if level is not None:
                await db.execute("UPDATE profiles SET level = ? WHERE user_id = ?", (level, user_id))
            if coins is not None:
                await db.execute("UPDATE profiles SET coins = ? WHERE user_id = ?", (coins, user_id))
            await db.commit()

    async def setup(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id INTEGER PRIMARY KEY,
                    messages INTEGER,
                    voice INTEGER,
                    xp INTEGER,
                    level INTEGER,
                    coins INTEGER
                )
            """)
            await db.commit()
