from discord.ext import commands
from .cog import AntiNukeCog

async def setup(bot):
    await bot.add_cog(AntiNukeCog(bot))
