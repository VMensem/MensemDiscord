from discord.ext import commands
from .commands import warn, ban

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(Moderation(bot))
    await warn.setup(bot)
    await ban.setup(bot)
