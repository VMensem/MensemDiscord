import discord
from .config import CONFIG

def create_clan_embed(title, description, fields=None):
    embed = discord.Embed(title=title, description=description, color=CONFIG["EMBED_COLOR"])
    embed.set_footer(text=CONFIG["FOOTER"])
    embed.timestamp = discord.utils.utcnow()
    if fields:
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
    return embed
