import sqlite3
import os

DB_PATH = "tickets/data/tickets.db"

def init_db():
    os.makedirs("tickets/data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS panels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                channel_id INTEGER,
                message_id INTEGER,
                title TEXT,
                description TEXT,
                color INTEGER
            );
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                panel_id INTEGER,
                name TEXT,
                description TEXT,
                emoji TEXT,
                target_category_id INTEGER,
                staff_role_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                channel_id INTEGER,
                category_id INTEGER,
                status TEXT DEFAULT 'open'
            );
        """)

def create_ticket(guild_id, user_id, channel_id, category_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO tickets (guild_id, user_id, channel_id, category_id, status)
            VALUES (?, ?, ?, ?, 'open')
            """,
            (guild_id, user_id, channel_id, category_id),
        )
        return cursor.lastrowid

def close_ticket(channel_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE tickets SET status = 'closed' WHERE channel_id = ?", (channel_id,))
