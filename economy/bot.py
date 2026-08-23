import discord
from discord.ext import commands
from .database import init_db
from .commands import balance

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        await init_db()

async def setup(bot):
    await bot.add_cog(Economy(bot))
    await balance.setup(bot)
