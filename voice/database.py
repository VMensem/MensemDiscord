from pathlib import Path

import aiosqlite


DATABASE = Path("voice/data/voice.db")


async def init_database():
    DATABASE.parent.mkdir(exist_ok=True, parents=True)

    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL UNIQUE,
                owner_id INTEGER NOT NULL,
                room_type TEXT NOT NULL,
                channel_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS personal_rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                channel_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
            """
        )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS couples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                channel_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
            """
        )

        await db.commit()


async def add_room(channel_id: int, owner_id: int, room_type: str, channel_name: str):
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            """
            INSERT INTO rooms (
                channel_id,
                owner_id,
                room_type,
                channel_name,
                is_active
            )
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(channel_id) DO UPDATE SET
                owner_id = excluded.owner_id,
                room_type = excluded.room_type,
                channel_name = excluded.channel_name,
                is_active = 1
            """,
            (channel_id, owner_id, room_type, channel_name),
        )
        await db.commit()


async def get_room(channel_id: int):
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM rooms
            WHERE channel_id = ?
            AND is_active = 1
            """,
            (channel_id,),
        )
        return await cursor.fetchone()


async def get_active_room(owner_id: int, room_type: str):
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM rooms
            WHERE owner_id = ?
            AND room_type = ?
            AND is_active = 1
            ORDER BY id DESC
            LIMIT 1
            """,
            (owner_id, room_type),
        )
        return await cursor.fetchone()


async def delete_room(channel_id: int):
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            """
            UPDATE rooms
            SET is_active = 0
            WHERE channel_id = ?
            """,
            (channel_id,),
        )
        await db.commit()


async def update_room_owner(channel_id: int, owner_id: int):
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            """
            UPDATE rooms
            SET owner_id = ?
            WHERE channel_id = ?
            """,
            (owner_id, channel_id),
        )
        await db.commit()


async def get_owner(channel_id: int):
    room = await get_room(channel_id)
    if room:
        return room["owner_id"]
    return None
