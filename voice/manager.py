import logging

import discord

from .database import (
    add_room,
    delete_room as mark_room_inactive,
    get_active_room,
    get_room,
    update_room_panel,
)
from .love import create_love
from .panel import send_panel, VoicePanel
from .personal import create_personal
from .private import create_private
from .report import create_report
from .sobes import create_sobes

logger = logging.getLogger(__name__)

created_channels: dict[int, dict[str, int | str]] = {}


async def _restore_existing_room(member, room_type: str):
    existing = await get_active_room(member.id, room_type)
    if existing is None:
        return None

    room_id = int(existing["channel_id"])
    room = member.guild.get_channel(room_id)
    if room is None:
        await mark_room_inactive(room_id)
        created_channels.pop(room_id, None)
        return None

    created_channels[room.id] = {"owner": member.id, "type": room_type}
    if member.voice is None or member.voice.channel != room:
        await member.move_to(room)

    panel_channel_id = existing["panel_channel_id"] if "panel_channel_id" in existing.keys() else None
    panel_channel = None
    if panel_channel_id:
        panel_channel = member.guild.get_channel(int(panel_channel_id))
    if panel_channel is None:
        try:
            panel_channel = await send_panel(room, member)
            if panel_channel is not None:
                await update_room_panel(room.id, panel_channel.id)
        except Exception:
            logging.exception("Failed to restore voice panel")
    return room


async def create_room(member, room_type):
    if getattr(member, "bot", False):
        return None

    restored = await _restore_existing_room(member, room_type)
    if restored is not None:
        return restored

    if room_type == "private":
        room = await create_private(member)
    elif room_type == "personal":
        room = await create_personal(member)
    elif room_type == "love":
        room = await create_love(member)
    elif room_type == "report":
        room = await create_report(member)
    elif room_type == "sobes":
        room = await create_sobes(member)
    else:
        return None

    if room is None:
        return None

    created_channels[room.id] = {"owner": member.id, "type": room_type}
    logger.info(f"[VOICE] Saving room to DB: {room.id}")
    await add_room(member.guild.id, room.id, member.id, room_type, room.name)
    logger.info("[VOICE] Room saved to DB")

    if member.voice is None or member.voice.channel != room:
        logger.info(f"[VOICE] Moving member to room: {room.id}")
        await member.move_to(room)
        logger.info("[VOICE] Member moved successfully")

    # Verify member is in the room
    # Discord can have a slight delay after move_to, so we check again.
    if member.voice and member.voice.channel == room:
        logger.info(f"[VOICE] Member verified in room: {room.id}")
        try:
            # Try to send panel directly to the voice channel's integrated text chat
            # This works if "Text in Voice" is enabled for the channel.
            embed = discord.Embed(
                title="Управление комнатой",
                description="Используй кнопки ниже для управления комнатой.",
                color=discord.Color.red(),
            )
            await room.send(embed=embed, view=VoicePanel(member.id))
            logger.info("[VOICE] Panel sent to voice channel text chat")
        except Exception:
            logger.exception("[VOICE] Failed to send panel to voice channel text chat")
    else:
        logger.warning(f"[VOICE] Member not found in room after move_to: {room.id}")

    return room


async def delete_room(channel):
    if channel is None or not isinstance(channel, discord.VoiceChannel):
        return

    logger.info(f"[VOICE] Attempting to delete room: {channel.id}, members count: {len(channel.members)}")
    if len(channel.members) != 0:
        logger.info(f"[VOICE] Room not empty, skipping deletion")
        return

    room = created_channels.get(channel.id)
    db_room = await get_room(channel.id)
    
    # db_room might be a Row object or dict-like, or sometimes a tuple depending on the driver.
    # The error suggests it's being treated as a tuple.
    # Let's ensure we can safely access panel_channel_id.
    
    panel_channel_id = None
    if db_room:
        # Check if db_room is a dict-like Row (asyncpg/aiosqlite)
        if hasattr(db_room, "get"):
            panel_channel_id = db_room.get("panel_channel_id")
        elif isinstance(db_room, (tuple, list)):
            # Fallback to index if it's a tuple. Schema index for panel_channel_id is 6
            # (room_id:0, guild_id:1, channel_id:2, owner_id:3, room_type:4, channel_name:5, panel_channel_id:6)
            try:
                panel_channel_id = db_room[6]
            except IndexError:
                logger.error(f"[VOICE] db_room tuple too short: {db_room}")
        else:
            logger.warning(f"[VOICE] Unexpected db_room type: {type(db_room)}")

    if room is None and db_room is None:
        logger.info(f"[VOICE] No room record found for {channel.id}")
        return

    logger.info(f"[VOICE] Proceeding with deletion for {channel.id}")
    
    try:
        await channel.delete()
        logger.info(f"[VOICE] Discord channel deleted: {channel.id}")
    except discord.NotFound:
        pass
    except Exception:
        logger.exception("Failed to delete voice room")
    finally:
        if panel_channel_id:
            logger.info(f"[VOICE] Found panel channel to delete: {panel_channel_id}")
            panel_channel = channel.guild.get_channel(int(panel_channel_id))
            if panel_channel is not None:
                try:
                    await panel_channel.delete()
                    logger.info(f"[VOICE] Panel channel deleted: {panel_channel_id}")
                except discord.NotFound:
                    pass
                except Exception:
                    logger.exception("Failed to delete linked voice panel")
        await mark_room_inactive(channel.id)
        created_channels.pop(channel.id, None)
        logger.info(f"[VOICE] Room {channel.id} marked inactive and removed from created_channels")
