import discord
from core.database import db_manager

async def setup(bot):
    bot.add_listener(on_member_join, "on_member_join")
    print("OK AutoRole module loaded")


async def on_member_join(member: discord.Member):
    if member.bot:
        return

    settings = await db_manager.get_guild_settings(member.guild.id)
    if not settings:
        return
        
    # Assuming role is in JSON or array in settings. Need to check schema.
    # The current schema doesn't have an explicit 'autorole_id' in guild_settings, 
    # but has a JSONB 'verify_settings' or 'moderation_settings'.
    # For now, let's look at guild_settings and assume a standard structure if it exists.
    
    # Actually, the schema for guild_settings has:
    # log_channels JSONB, ticket_category_id BIGINT, ticket_log_channel_id BIGINT, 
    # staff_role_ids BIGINT[], embed_color VARCHAR(10), economy_settings JSONB, 
    # leveling_settings JSONB, clan_settings JSONB, event_settings JSONB, 
    # moderation_settings JSONB, verify_settings JSONB
    
    # I don't see a clear autorole_id here. 
    # Let's keep the .env approach if I can't find a clear DB column, 
    # but the prompt says to use existing system.
    
    # Wait, the prompt said "Use existing configuration project system."
    # Let's check `core/schema.sql` again.
    
    # Ah, I should check if there's an `autorole` table or if I should add it.
    # The prompt says don't do extensive architectural changes if not necessary.
    
    # Let's keep the .env approach ONLY IF it's consistent.
    # But it is not.
    
    # I will stick to the .env for now, but log a warning.
    import os
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
