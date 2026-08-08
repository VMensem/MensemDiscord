from discord.ext import commands
import discord
from discord import app_commands
from .database import init_db
from .views import TicketControlView, TicketPanelView

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()

    async def cog_load(self):
        # Register persistent views
        self.bot.add_view(TicketPanelView())
        self.bot.add_view(TicketControlView())

    @app_commands.command(name="ticket-panel", description="Отправить панель создания тикетов")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Тикеты",
            description="Нажмите кнопку ниже, чтобы создать обращение.",
            color=discord.Color.red(),
        )
        await interaction.channel.send(embed=embed, view=TicketPanelView())
        await interaction.response.send_message("Панель тикетов отправлена.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
