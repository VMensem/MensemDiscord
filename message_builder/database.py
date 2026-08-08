import sqlite3
import os

DB_PATH = "message_builder/data/templates.db"

def init_db():
    os.makedirs("message_builder/data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                json_data TEXT
            )
        """)
