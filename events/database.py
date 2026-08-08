import json
import os
import sqlite3
from datetime import datetime


DB_PATH = "events/data/events.db"


def init_db():
    os.makedirs("events/data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                creator_id INTEGER,
                title TEXT,
                type TEXT,
                status TEXT DEFAULT 'pending',
                channel_id INTEGER,
                message_id INTEGER,
                settings TEXT,
                created_at DATETIME
            );
            CREATE TABLE IF NOT EXISTS participants (
                event_id INTEGER,
                user_id INTEGER,
                is_reserve INTEGER DEFAULT 0,
                registered_at DATETIME
            );
            CREATE TABLE IF NOT EXISTS winners (
                event_id INTEGER,
                user_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS reminders (
                event_id INTEGER,
                time_offset INTEGER,
                sent INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS event_history (
                event_id INTEGER,
                action TEXT,
                actor_id INTEGER,
                details TEXT,
                timestamp DATETIME
            );
            """
        )
        conn.commit()


def create_event(
    guild_id: int,
    creator_id: int,
    title: str,
    event_type: str,
    channel_id: int | None,
    message_id: int | None,
    settings: dict,
) -> int:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO events (
                guild_id,
                creator_id,
                title,
                type,
                status,
                channel_id,
                message_id,
                settings,
                created_at
            )
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?)
            """,
            (
                guild_id,
                creator_id,
                title,
                event_type,
                channel_id,
                message_id,
                json.dumps(settings, ensure_ascii=False),
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def add_event_history(event_id: int, action: str, actor_id: int, details: str) -> None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO event_history (
                event_id,
                action,
                actor_id,
                details,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_id, action, actor_id, details, datetime.utcnow().isoformat(timespec="seconds")),
        )
        conn.commit()


def count_events(guild_id: int | None = None) -> tuple[int, int]:
    init_db()
    query = "SELECT COUNT(*), SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) FROM events"
    params: tuple[int, ...] = ()
    if guild_id is not None:
        query += " WHERE guild_id = ?"
        params = (guild_id,)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        total, pending = cursor.fetchone()
        return int(total or 0), int(pending or 0)
