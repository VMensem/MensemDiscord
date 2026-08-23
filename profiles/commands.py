import discord
from discord import app_commands
from .generator import ProfileGenerator
from .database import ProfileDatabase

class ProfileCommands:
    def __init__(self, bot):
        self.bot = bot
        self.db = ProfileDatabase()
        self.generator = ProfileGenerator()
        
        # Register the command directly with the bot tree
        @self.bot.tree.command(name="profile", description="Посмотреть профиль пользователя")
        @app_commands.describe(member="Участник, чей профиль вы хотите посмотреть")
        async def profile(interaction: discord.Interaction, member: discord.Member = None):
            member = member or interaction.user
            
            # Get stats
            stats = await self.db.get_profile(member.id, interaction.guild_id)
            if not stats:
                await self.db.ensure_profile(member.id, interaction.guild_id)
                stats = await self.db.get_profile(member.id, interaction.guild_id)
            
            # Generate image
            image_buffer = await self.generator.generate(member, stats)
            
            # Send
            await interaction.response.send_message(file=discord.File(image_buffer, filename="profile.png"))
