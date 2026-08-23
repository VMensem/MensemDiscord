from discord.ext import commands
from .database import init_db
from .views import ClanManageView
from .commands import admin, clan, management

class Clans(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        await init_db()
        self.bot.add_view(ClanManageView())

async def setup(bot):
    await bot.add_cog(Clans(bot))
    await clan.setup(bot)
    await management.setup(bot)
    await admin.setup(bot)
