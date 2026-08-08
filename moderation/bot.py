from discord.ext import commands
from .database import init_db
from .commands import warn

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()

async def setup(bot):
    await bot.add_cog(Moderation(bot))
    await warn.setup(bot)
