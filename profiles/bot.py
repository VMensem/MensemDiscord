import discord
from discord.ext import commands
from .commands import ProfileCommands

class ProfilesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Инициализация команды профиля
        self.profile_commands = ProfileCommands(bot)

    async def cog_load(self):
        print("Profiles Cog loaded")

async def setup(bot):
    await bot.add_cog(ProfilesCog(bot))
