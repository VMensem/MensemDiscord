from __future__ import annotations

import os

import discord
from discord import app_commands
from discord.ext import commands

from .config import configured_staff_role_ids
from .views import StaffRecruitmentPanel, build_setup_embed, register_open_application_views
from .database import init_db


def get_env_int(key: str, default: int = 0) -> int:
    raw = os.getenv(key, "").strip()
    return int(raw) if raw.isdigit() else default


class Staff(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup_staff", description="Отправить панель набора в staff")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_staff(self, interaction: discord.Interaction):
        if interaction.guild is None or interaction.channel is None or not hasattr(interaction.channel, "send"):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Ошибка",
                    description="Команда доступна только в текстовом канале на сервере.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            await interaction.channel.send(embed=build_setup_embed(), view=StaffRecruitmentPanel())
        except (discord.Forbidden, discord.HTTPException):
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Ошибка",
                    description="Не удалось отправить панель в этот канал.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        await interaction.followup.send(
            embed=discord.Embed(
                title="Готово",
                description="Панель набора отправлена в этот канал.",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

    @app_commands.command(name="staff", description="Показать активный состав staff")
    async def staff(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Ошибка",
                    description="Команда доступна только на сервере.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        role_ids = configured_staff_role_ids()
        members = [
            member
            for member in guild.members
            if any(role.id in role_ids for role in member.roles)
        ]
        online = [member for member in members if member.status is not discord.Status.offline]

        embed = discord.Embed(title="Staff", color=discord.Color.red())
        embed.add_field(name="Всего", value=str(len(members)), inline=True)
        embed.add_field(name="Онлайн", value=str(len(online)), inline=True)
        if online:
            embed.description = "\n".join(member.mention for member in online[:20])
        else:
            embed.description = "Онлайн staff сейчас не найден."

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await init_db()
    await register_open_application_views(bot)
    bot.add_view(StaffRecruitmentPanel())
    await bot.add_cog(Staff(bot))
