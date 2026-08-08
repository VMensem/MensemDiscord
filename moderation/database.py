import sqlite3
import os

DB_PATH = "moderation/data/moderation.db"

def init_db():
    os.makedirs("moderation/data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS cases (
                case_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                mod_id INTEGER,
                type TEXT,
                reason TEXT,
                timestamp DATETIME
            );
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                case_id INTEGER,
                reason TEXT
            );
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                author_id INTEGER,
                note TEXT,
                timestamp DATETIME
            );
            CREATE TABLE IF NOT EXISTS case_edits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                mod_id INTEGER,
                field TEXT,
                old_val TEXT,
                new_val TEXT,
                timestamp DATETIME
            );
        """)

def add_case(guild_id, user_id, mod_id, type, reason):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "INSERT INTO cases (guild_id, user_id, mod_id, type, reason, timestamp) VALUES (?,?,?,?,?,datetime('now'))",
            (guild_id, user_id, mod_id, type, reason)
        )
        return cursor.lastrowid
