import aiosqlite
import os

DB_PATH = "economy/data/economy.db"

async def init_db():
    os.makedirs("economy/data", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                guild_id INTEGER, user_id INTEGER, balance INTEGER DEFAULT 1000, 
                bank INTEGER DEFAULT 0, total_earned INTEGER DEFAULT 0, total_spent INTEGER DEFAULT 0,
                created_at DATETIME, PRIMARY KEY (guild_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER, 
                type TEXT, amount INTEGER, reason TEXT, created_at DATETIME
            );
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price INTEGER, type TEXT, created_at DATETIME
            );
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, item_id INTEGER, amount INTEGER
            );
            CREATE TABLE IF NOT EXISTS cooldowns (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, command TEXT, expires_at REAL
            );
        """)
