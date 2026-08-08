import discord
from discord import app_commands
from discord.ext import commands


class ServerManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="server", description="Показать состояние сервера")
    async def server(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)

        embed = discord.Embed(title=guild.name, color=discord.Color.red())
        embed.add_field(name="Участников", value=str(guild.member_count or len(guild.members)))
        embed.add_field(name="Каналов", value=str(len(guild.channels)))
        embed.add_field(name="Ролей", value=str(len(guild.roles)))
        embed.add_field(name="Бустов", value=str(guild.premium_subscription_count or 0))
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ServerManagement(bot))
