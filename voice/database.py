from core.database import db_manager

async def init_database():
    pass

async def add_room(guild_id: int, channel_id: int, owner_id: int, room_type: str, channel_name: str, panel_channel_id: int | None = None):
    await db_manager.execute(
        """
        INSERT INTO voice_rooms (guild_id, channel_id, owner_id, room_type, channel_name, panel_channel_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (channel_id) DO UPDATE SET 
            owner_id = excluded.owner_id, 
            room_type = excluded.room_type, 
            channel_name = excluded.channel_name, 
            panel_channel_id = excluded.panel_channel_id, 
            is_active = TRUE
        """,
        guild_id, channel_id, owner_id, room_type, channel_name, panel_channel_id
    )

async def get_room(channel_id: int):
    return await db_manager.fetchrow(
        "SELECT * FROM voice_rooms WHERE channel_id = $1 AND is_active = TRUE",
        channel_id
    )

async def get_active_room(owner_id: int, room_type: str):
    return await db_manager.fetchrow(
        "SELECT * FROM voice_rooms WHERE owner_id = $1 AND room_type = $2 AND is_active = TRUE ORDER BY room_id DESC LIMIT 1",
        owner_id, room_type
    )

async def delete_room(channel_id: int):
    await db_manager.execute(
        "UPDATE voice_rooms SET is_active = FALSE WHERE channel_id = $1",
        channel_id
    )

async def update_room_owner(channel_id: int, owner_id: int):
    await db_manager.execute(
        "UPDATE voice_rooms SET owner_id = $1 WHERE channel_id = $2",
        owner_id, channel_id
    )

async def update_room_panel(channel_id: int, panel_channel_id: int | None):
    await db_manager.execute(
        "UPDATE voice_rooms SET panel_channel_id = $1 WHERE channel_id = $2",
        panel_channel_id, channel_id
    )

async def get_owner(channel_id: int):
    room = await get_room(channel_id)
    return room["owner_id"] if room else None

