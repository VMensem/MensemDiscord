from discord.ext import commands
from .database import init_db
from .views import ReportPanelButton, TicketControlView
from .commands import panel

class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()

    async def cog_load(self):
        self.bot.add_view(ReportPanelButton())
        self.bot.add_view(TicketControlView())

async def setup(bot):
    await bot.add_cog(Reports(bot))
    await panel.setup(bot)
