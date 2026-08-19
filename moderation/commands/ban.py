import discord
from discord import app_commands
from core.database import db_manager

async def setup(bot):
    @bot.tree.command(name="ban", description="Забанить пользователя")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):
        # Hierarchy Checks
        if member == interaction.user:
            return await interaction.response.send_message("Вы не можете забанить себя.", ephemeral=True)
        if member == interaction.guild.owner:
            return await interaction.response.send_message("Нельзя забанить владельца сервера.", ephemeral=True)
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("У пользователя роль выше или равна вашей.", ephemeral=True)
        if member.top_role >= interaction.guild.me.top_role:
            return await interaction.response.send_message("У пользователя роль выше или равна роли бота.", ephemeral=True)
        
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"Пользователь {member.mention} забанен.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("У меня недостаточно прав.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ошибка: {e}", ephemeral=True)
