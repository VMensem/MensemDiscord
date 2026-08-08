from discord.ext import commands
from .database import init_db
from .views import MainEventMenu
from .commands import event

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()

    async def cog_load(self):
        self.bot.add_view(MainEventMenu())

async def setup(bot):
    await bot.add_cog(Events(bot))
    await event.setup(bot)
