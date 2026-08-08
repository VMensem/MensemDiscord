import discord

async def scan_guild(guild: discord.Guild):
    return {
        "channels": {c.name: c.id for c in guild.text_channels},
        "roles": {r.name: r.id for r in guild.roles},
        "categories": {c.name: c.id for c in guild.categories}
    }
