import discord
from discord.ext import commands
from .commands import ProfileCommands
from .database import ProfileDatabase

class ProfilesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = ProfileDatabase()
        # Инициализация команды профиля
        self.profile_commands = ProfileCommands(bot)

    async def cog_load(self):
        # Инициализация базы данных теперь в async контексте
        await self.db.setup()
        print("Profiles Cog loaded and DB setup complete")

async def setup(bot):
    await bot.add_cog(ProfilesCog(bot))
