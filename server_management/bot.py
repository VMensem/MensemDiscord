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

        embed = discord.Embed(title=f"🏠 {guild.name}", description="*Информация о Discord-сервере*", color=discord.Color.red())
        
        embed.add_field(name="👥 Участники", value=f"`{guild.member_count or len(guild.members)}`", inline=True)
        embed.add_field(name="💬 Каналы", value=f"`{len(guild.channels)}`", inline=True)
        embed.add_field(name="🎭 Роли", value=f"`{len(guild.roles)}`", inline=True)
        embed.add_field(name="🚀 Бусты", value=f"`{guild.premium_subscription_count or 0}`", inline=True)

        if guild.owner:
            embed.add_field(name="👑 Владелец", value=f"`{guild.owner.name}`", inline=True)
            
        embed.add_field(name="📅 Создан", value=f"`{guild.created_at.strftime('%d.%m.%Y')}`", inline=True)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        from datetime import datetime
        now = datetime.now().strftime("%H:%M")
        embed.set_footer(text=f"Mensem • Server Info • {now}")
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ServerManagement(bot))
