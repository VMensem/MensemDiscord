import discord
from discord import app_commands
from discord.ext import commands

from ..embeds import create_event_menu_embed
from ..permissions import is_event_manager
from ..views import MainEventMenu


class EventGroup(commands.GroupCog, group_name="event"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="menu", description="Главное меню управления событиями")
    async def menu(self, interaction: discord.Interaction):
        if not is_event_manager(interaction):
            return await interaction.response.send_message("Нет прав.", ephemeral=True)
        if interaction.guild is None:
            return await interaction.response.send_message("Команда работает только на сервере.", ephemeral=True)

        embed = create_event_menu_embed(interaction.guild, interaction.user)
        await interaction.response.send_message(embed=embed, view=MainEventMenu(), ephemeral=True)


async def setup(bot):
    await bot.add_cog(EventGroup(bot))
