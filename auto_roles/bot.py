import os

import discord


async def setup(bot):
    bot.add_listener(on_member_join, "on_member_join")
    print("OK AutoRole module loaded")


async def on_member_join(member: discord.Member):
    if member.bot:
        return

    unverify_role_id = int(os.getenv("VERIFY_ROLE_UNVERIFY", 0))
    if not unverify_role_id:
        return

    role = member.guild.get_role(unverify_role_id)
    if not role:
        return

    try:
        await member.add_roles(role, reason="AutoRole: add Unverify on join")
    except (discord.Forbidden, discord.HTTPException):
        pass
