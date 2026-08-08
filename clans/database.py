import aiosqlite
import os

DB_PATH = "clans/data/clans.db"

async def init_db():
    os.makedirs("clans/data", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS clans (
                id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, clan_id TEXT, name TEXT,
                tag TEXT, owner_id INTEGER, level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0,
                balance INTEGER DEFAULT 0, created_at DATETIME
            );
            CREATE TABLE IF NOT EXISTS clan_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT, clan_id INTEGER, user_id INTEGER, role TEXT, joined_at DATETIME
            );
            CREATE TABLE IF NOT EXISTS clan_invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT, clan_id INTEGER, user_id INTEGER, created_at DATETIME
            );
            CREATE TABLE IF NOT EXISTS clan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, clan_id INTEGER, action TEXT, user_id INTEGER, date DATETIME
            );
            CREATE TABLE IF NOT EXISTS clan_wars (
                id INTEGER PRIMARY KEY AUTOINCREMENT, clan_one INTEGER, clan_two INTEGER, status TEXT, winner INTEGER, date DATETIME
            );
        """)
