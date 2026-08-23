import logging
import os
import discord
from core.database import db_manager

def setup(bot):
    @bot.listen("on_member_join")
    async def on_member_join(member: discord.Member):
        print(f"DEBUG: on_member_join triggered for {member.name}")
        logging.info(f"on_member_join triggered for {member.name} ({member.id})")
        if member.bot:
            print("DEBUG: Member is a bot, returning")
            return
        
        unverify_role_id = int(os.getenv("VERIFY_ROLE_UNVERIFY", 0))
        print(f"DEBUG: Unverify role ID: {unverify_role_id}")
        logging.info(f"Unverify role ID from env: {unverify_role_id}")
        if not unverify_role_id:
            print("DEBUG: VERIFY_ROLE_UNVERIFY not set")
            logging.warning("VERIFY_ROLE_UNVERIFY not set in .env")
            return

        role = member.guild.get_role(unverify_role_id)
        if not role:
            print(f"DEBUG: Role {unverify_role_id} not found")
            logging.warning(f"Role {unverify_role_id} not found in guild {member.guild.name}")
            return

        try:
            await member.add_roles(role, reason="AutoRole: add Unverify on join")
            print(f"DEBUG: Successfully added role {role.name} to {member.name}")
            logging.info(f"Successfully added role {role.name} to {member.name}")
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"DEBUG: Failed to add role: {e}")
            logging.error(f"Failed to add role to {member.name}: {e}")
    print("OK AutoRole module loaded")
