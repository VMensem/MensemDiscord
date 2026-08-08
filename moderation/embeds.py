import discord

def create_embed(title, description, color=discord.Color.red()):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="Moderation System")
    embed.timestamp = discord.utils.utcnow()
    return embed
