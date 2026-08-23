import discord
from .config import CONFIG
import os

def create_report_embed(title, description):
    embed = discord.Embed(title=title, description=description, color=CONFIG["EMBED_COLOR"])
    embed.set_footer(text=os.getenv("REPORT_EMBED_FOOTER", "Mensem Reports System"))
    embed.timestamp = discord.utils.utcnow()
    return embed
