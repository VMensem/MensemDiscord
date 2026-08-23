import logging
import os
import discord
from core.database import db_manager

async def setup(bot):
    bot.add_listener(on_member_join, "on_member_join")
    print("OK AutoRole module loaded")


async def on_member_join(member: discord.Member):
    if member.bot:
        return
    
    logging.info(f"on_member_join triggered for {member.name} ({member.id})")

    settings = await db_manager.get_guild_settings(member.guild.id)
    if not settings:
        logging.info(f"No settings found for guild {member.guild.id}")
        return
        
    unverify_role_id = int(os.getenv("VERIFY_ROLE_UNVERIFY", 0))
    logging.info(f"Unverify role ID from env: {unverify_role_id}")
    if not unverify_role_id:
        logging.warning("VERIFY_ROLE_UNVERIFY not set in .env")
        return

    role = member.guild.get_role(unverify_role_id)
    if not role:
        logging.warning(f"Role {unverify_role_id} not found in guild {member.guild.name}")
        return

    try:
        await member.add_roles(role, reason="AutoRole: add Unverify on join")
        logging.info(f"Successfully added role {role.name} to {member.name}")
    except (discord.Forbidden, discord.HTTPException) as e:
        logging.error(f"Failed to add role to {member.name}: {e}")
