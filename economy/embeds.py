import discord
from .config import CONFIG

def create_economy_embed(title, description):
    embed = discord.Embed(title=title, description=description, color=CONFIG["EMBED_COLOR"])
    embed.set_footer(text=CONFIG["FOOTER"])
    embed.timestamp = discord.utils.utcnow()
    return embed
