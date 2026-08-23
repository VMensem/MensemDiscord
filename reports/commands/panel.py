import discord
from discord import app_commands
from ..embeds import create_report_embed
from ..views import ReportPanelButton

async def setup(bot):
    @bot.tree.command(name="report", description="Управление репортами")
    @app_commands.checks.has_permissions(administrator=True)
    async def report(interaction: discord.Interaction, action: str = "panel"):
        if action == "panel":
            embed = create_report_embed("🚨 Жалоба", "Если вы нашли нарушение правил сервера — создайте репорт.")
            await interaction.channel.send(embed=embed, view=ReportPanelButton())
            await interaction.response.send_message("Панель создана.", ephemeral=True)
