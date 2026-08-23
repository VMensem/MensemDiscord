import discord
from discord import app_commands

from ..views import ClanManageView


@app_commands.command(name="manage", description="Управление кланом")
async def manage(interaction: discord.Interaction):
    await interaction.response.send_message(view=ClanManageView(), ephemeral=True)


async def setup(bot):
    clan_group = bot.tree.get_command("clan")
    if clan_group is None:
        clan_group = app_commands.Group(name="clan", description="Команды кланов")
        bot.tree.add_command(clan_group)

    if clan_group.get_command("manage") is None:
        clan_group.add_command(manage)
