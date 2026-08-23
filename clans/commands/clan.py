import discord
from discord import app_commands
from discord.ext import commands
from ..embeds import create_clan_embed
from ..services.clan_service import create_new_clan
from ..services.clan_bank import deposit_to_clan, withdraw_from_clan
from ..views.top_view import ClanTopView
from ..database import get_clan_by_id, get_clan_members, get_clans_by_guild
from ..views.settings_view import ClanSettingsView

class CreateClanModal(discord.ui.Modal, title="Создание клана"):
    name = discord.ui.TextInput(label="Название клана", min_length=3, max_length=20)
    tag = discord.ui.TextInput(label="Тег клана", min_length=2, max_length=4)
    description = discord.ui.TextInput(label="Описание", style=discord.TextStyle.paragraph, max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        success = await create_new_clan(
            interaction.guild, 
            interaction.user, 
            str(self.name.value), 
            str(self.tag.value), 
            str(self.description.value)
        )
        if success:
            await interaction.followup.send(f"Клан {self.name.value} [{self.tag.value}] создан!", ephemeral=True)
        else:
            await interaction.followup.send("Ошибка при создании клана.", ephemeral=True)

class ClanCommands(commands.GroupCog, group_name="clan"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create", description="Создать клан")
    async def create(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CreateClanModal())
    
    @app_commands.command(name="info", description="Информация о клане")
    async def info(self, interaction: discord.Interaction, clan_id: int):
        clan = await get_clan_by_id(clan_id)
        if not clan:
            return await interaction.response.send_message("Клан не найден.", ephemeral=True)
        members = await get_clan_members(clan_id)
        embed = create_clan_embed(f"{clan['name']} [{clan['tag']}]", f"Level: {clan['level']}\nXP: {clan['xp']}\nMembers: {len(members)}")
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="deposit", description="Пополнить банк клана")
    async def deposit(self, interaction: discord.Interaction, clan_id: int, amount: int):
        success = await deposit_to_clan(interaction.guild_id, interaction.user.id, clan_id, amount)
        if success:
            await interaction.response.send_message(f"Успешно внесено {amount} в банк клана.", ephemeral=True)
        else:
            await interaction.response.send_message("Ошибка: Недостаточно средств или клан не найден.", ephemeral=True)
            
    @app_commands.command(name="withdraw", description="Снять средства из банка клана")
    async def withdraw(self, interaction: discord.Interaction, clan_id: int, amount: int):
        success = await withdraw_from_clan(interaction.guild_id, interaction.user.id, clan_id, amount)
        if success:
            await interaction.response.send_message(f"Успешно снято {amount} из банка клана.", ephemeral=True)
        else:
            await interaction.response.send_message("Ошибка: Недостаточно средств или нет прав.", ephemeral=True)

    @app_commands.command(name="settings", description="Настройки клана")
    async def settings(self, interaction: discord.Interaction, clan_id: int):
        clan = await get_clan_by_id(clan_id)
        if not clan:
            return await interaction.response.send_message("Клан не найден.", ephemeral=True)
        
        if clan['leader_id'] != interaction.user.id:
            return await interaction.response.send_message("Настройки доступны только лидеру клана.", ephemeral=True)
            
        await interaction.response.send_message("Выберите настройку:", view=ClanSettingsView(clan_id), ephemeral=True)

    @app_commands.command(name="top", description="Топ кланов")
    async def top(self, interaction: discord.Interaction):
        clans = await get_clans_by_guild(interaction.guild_id)
        if not clans:
            return await interaction.response.send_message("Кланов пока нет.", ephemeral=True)
        view = ClanTopView(clans)
        await interaction.response.send_message(embed=view.get_embed(), view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ClanCommands(bot))
