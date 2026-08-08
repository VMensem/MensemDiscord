import discord
from discord import app_commands
from discord.ext import commands
from ..embeds import create_clan_embed

class CreateClanModal(discord.ui.Modal, title="Создание клана"):
    name = discord.ui.TextInput(label="Название клана", min_length=3, max_length=20)
    tag = discord.ui.TextInput(label="Тег клана", min_length=2, max_length=4)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Клан {self.name.value} [{self.tag.value}] создан!", ephemeral=True)

class ClanCommands(commands.GroupCog, group_name="clan"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create", description="Создать клан")
    async def create(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CreateClanModal())
    
    @app_commands.command(name="info", description="Информация о клане")
    async def info(self, interaction: discord.Interaction):
        embed = create_clan_embed("🏰 Mensem Legends [MNSM]", "Level: 5\nXP: 25000\nMembers: 15/20")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ClanCommands(bot))
