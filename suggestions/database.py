import sqlite3
import os
import json
from datetime import datetime

DB_PATH = "suggestions/data/suggestions.db"

def init_db():
    os.makedirs("suggestions/data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                author_id INTEGER,
                channel_id INTEGER,
                title TEXT,
                description TEXT,
                status TEXT DEFAULT '🟡 На рассмотрении',
                comment TEXT,
                admin_id INTEGER,
                votes_up TEXT DEFAULT '[]',
                votes_down TEXT DEFAULT '[]',
                created_at TIMESTAMP
            )
        """)

def get_config(key):
    with sqlite3.connect(DB_PATH) as conn:
        res = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
        return res[0] if res else None

def set_config(key, value):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))

def add_suggestion(author_id, channel_id, title, description):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "INSERT INTO suggestions (author_id, channel_id, title, description, created_at) VALUES (?, ?, ?, ?, ?)",
            (author_id, channel_id, title, description, datetime.now())
        )
        return cursor.lastrowid

def update_suggestion(id, **kwargs):
    fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [id]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"UPDATE suggestions SET {fields} WHERE id = ?", values)

def get_suggestion(id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute("SELECT * FROM suggestions WHERE id = ?", (id,)).fetchone()

def get_suggestion_by_message(message_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute("SELECT * FROM suggestions WHERE message_id = ?", (message_id,)).fetchone()

def get_recent_suggestions(limit=10):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute("SELECT * FROM suggestions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
