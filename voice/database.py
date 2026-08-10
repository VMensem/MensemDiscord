from core.database import db_manager

async def init_database():
    pass

async def add_room(guild_id: int, channel_id: int, owner_id: int, room_type: str, channel_name: str, panel_channel_id: int | None = None):
    await db_manager.execute(
        """
        INSERT INTO voice_rooms (guild_id, channel_id, owner_id, room_type, channel_name, panel_channel_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (channel_id) DO UPDATE SET owner_id = $3, room_type = $4, channel_name = $5, panel_channel_id = $6, is_active = TRUE
        """,
        guild_id, channel_id, owner_id, room_type, channel_name, panel_channel_id
    )

async def get_room(channel_id: int):
    return await db_manager.fetchrow(
        "SELECT * FROM voice_rooms WHERE channel_id = $1 AND is_active = TRUE",
        channel_id
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
