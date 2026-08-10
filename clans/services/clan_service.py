import discord
from ..database import create_clan, add_clan_member

async def create_new_clan(guild: discord.Guild, leader: discord.Member, name: str, tag: str, description: str) -> bool:
    # 1. Create Discord structure
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        leader: discord.PermissionOverwrite(view_channel=True, manage_channels=True, manage_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True, manage_roles=True),
    }

    category = await guild.create_category(f"Clan — {name}", overwrites=overwrites)
    text_channel = await guild.create_text_channel(f"{name}-chat", category=category)
    voice_channel = await guild.create_voice_channel(name, category=category)
    role = await guild.create_role(name=name)
    await leader.add_roles(role)

    # 2. Save to DB
    clan_id = await create_clan(guild.id, name, tag, description, leader.id)
    # Need to update DB with Discord IDs
    # (Simplified for now, will enhance schema/db functions)

    # 3. Add member
    await add_clan_member(clan_id, leader.id)

    return True
