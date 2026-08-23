import asyncio
import logging
from typing import Any

import discord

from .love import create_love
# from .panel import send_panel, VoicePanel - REMOVED TO BREAK CYCLE
from .personal import create_personal
from .private import create_private
from .report import create_report
from .sobes import create_sobes

logger = logging.getLogger(__name__)

# Temporary room data: channel_id -> {owner_id, room_type, panel_channel_id}
temporary_rooms: dict[int, dict[str, Any]] = {}
cleanup_tasks: dict[int, asyncio.Task] = {}
# ... (rest of the file)


async def get_owner(channel_id: int) -> int | None:
    room = temporary_rooms.get(channel_id)
    return room["owner_id"] if room else None


async def update_room_owner(channel_id: int, owner_id: int) -> None:
    if channel_id in temporary_rooms:
        temporary_rooms[channel_id]["owner_id"] = owner_id
        logger.info(f"[VOICE] Room owner updated: {channel_id} -> {owner_id}")


async def create_room(member, room_type):
    from .panel import send_panel, VoicePanel

    if getattr(member, "bot", False):
        return None

    logger.info(f"[VOICE] Creating temporary room of type: {room_type}")

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
        logger.warning(f"[VOICE] Unknown room type: {room_type}")
        return None

    if room is None:
        logger.error(f"[VOICE] Failed to create Discord channel for type: {room_type}")
        return None

    logger.info(f"[VOICE] Room created: {room.id}")

    temporary_rooms[room.id] = {
        "guild_id": member.guild.id,
        "owner_id": member.id,
        "room_type": room_type,
        "panel_channel_id": None
    }
    logger.info(f"[VOICE] Room registered in temporary_rooms: {room.id}")

    if member.voice is None or member.voice.channel != room:
        logger.info(f"[VOICE] Moving member to room: {room.id}")
        await member.move_to(room)
        logger.info(f"[VOICE] Member moved successfully")

    if member.voice and member.voice.channel == room:
        try:
            await send_panel(room, member)
            logger.info("[VOICE] Panel sent to voice channel text chat")
        except Exception:
            logging.exception("[VOICE] Failed to send panel")

    return room


async def _schedule_cleanup(channel_id: int, guild: discord.Guild):
    logger.info(f"[VOICE] Cleanup scheduled: channel={channel_id}")
    await asyncio.sleep(0.75)
    logger.info(f"[VOICE] Cleanup waiting: channel={channel_id}")

    channel = guild.get_channel(channel_id)
    if channel is None:
        logger.info(f"[VOICE] Cleanup channel not found: channel={channel_id}")
        temporary_rooms.pop(channel_id, None)
        cleanup_tasks.pop(channel_id, None)
        return

    human_members = [m for m in channel.members if not m.bot]
    logger.info(f"[VOICE] Cleanup members: channel={channel_id} members={len(channel.members)} (humans: {len(human_members)})")
    
    if len(human_members) != 0:
        logger.info(f"[VOICE] Cleanup cancelled: channel={channel_id} not empty")
        cleanup_tasks.pop(channel_id, None)
        return

    logger.info(f"[VOICE] Cleanup deleting: channel={channel_id}")
    try:
        room_data = temporary_rooms.get(channel_id)
        if room_data:
            await channel.delete()
            panel_channel_id = room_data.get("panel_channel_id")
            if panel_channel_id:
                panel_channel = guild.get_channel(int(panel_channel_id))
                if panel_channel:
                    await panel_channel.delete()
        logger.info(f"[VOICE] Cleanup deleted: channel={channel_id}")
    except discord.NotFound:
        logger.info(f"[VOICE] Cleanup channel already gone: channel={channel_id}")
    except Exception as e:
        logger.error(f"[VOICE] Cleanup delete failed: channel={channel_id} error={e}")
    finally:
        temporary_rooms.pop(channel_id, None)
        cleanup_tasks.pop(channel_id, None)


async def delete_room(channel):
    logger.info(f"[VOICE] Cleanup check: channel={channel.id}")
    if channel is None or not isinstance(channel, discord.VoiceChannel):
        logger.info(f"[VOICE] Not a voice channel or None: {channel}")
        return

    if channel.id not in temporary_rooms:
        return

    if channel.id in cleanup_tasks:
        return

    task = asyncio.create_task(_schedule_cleanup(channel.id, channel.guild))
    cleanup_tasks[channel.id] = task
