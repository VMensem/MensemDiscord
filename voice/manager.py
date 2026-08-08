import logging

import discord

from .database import add_room, delete_room as mark_room_inactive, get_active_room, get_room
from .love import create_love
from .panel import send_panel
from .personal import create_personal
from .private import create_private
from .report import create_report
from .sobes import create_sobes


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
    await add_room(room.id, member.id, room_type, room.name)

    if member.voice is None or member.voice.channel != room:
        await member.move_to(room)

    try:
        await send_panel(room, member)
    except Exception:
        logging.exception("Failed to send voice panel")

    return room


async def delete_room(channel):
    if channel is None or not isinstance(channel, discord.VoiceChannel):
        return

    if len(channel.members) != 0:
        return

    room = created_channels.get(channel.id)
    db_room = await get_room(channel.id)
    if room is None and db_room is None:
        return

    try:
        await channel.delete()
    except discord.NotFound:
        pass
    except Exception:
        logging.exception("Failed to delete voice room")
    finally:
        await mark_room_inactive(channel.id)
        created_channels.pop(channel.id, None)
