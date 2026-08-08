# banner/stats.py
import discord

async def get_guild_stats(guild: discord.Guild) -> dict:
    # Members
    members = guild.member_count
    
    # Online
    online = sum(1 for m in guild.members if m.status != discord.Status.offline)
    
    # Voice Online
    voice_online = sum(len(vc.members) for vc in guild.voice_channels)
    
    # Boosts
    boosts = guild.premium_subscription_count
    
    return {
        "members": members,
        "online": online,
        "voice": voice_online,
        "boosts": boosts
    }
