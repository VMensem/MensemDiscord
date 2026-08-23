import discord
from discord import app_commands
from discord.ext import commands
from .database import AntiNukeDatabase
from .detector import AntiNukeDetector

class AntiNukeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = AntiNukeDatabase()
        self.detector = AntiNukeDetector(bot, self.db)

    async def cog_load(self):
        self.detector.cleanup_task.start()

    def cog_unload(self):
        self.detector.cleanup_task.cancel()

    antinuke_group = app_commands.Group(name="antinuke", description="Anti-Nuke management")
    whitelist_group = app_commands.Group(name="whitelist", description="Manage whitelist", parent=antinuke_group)
    trusted_group = app_commands.Group(name="trusted", description="Manage trusted users", parent=antinuke_group)

    @antinuke_group.command(name="set-alert-channel", description="Set channel for alerts")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_alert_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.db.update_settings(interaction.guild_id, alert_channel_id=channel.id)
        await interaction.response.send_message(f"Alert channel set to {channel.mention}.", ephemeral=True)

    @antinuke_group.command(name="status", description="Show Anti-Nuke status")
    @app_commands.checks.has_permissions(administrator=True)
    async def status(self, interaction: discord.Interaction):
        settings = await self.db.get_settings(interaction.guild_id)
        if not settings:
            await interaction.response.send_message("Anti-Nuke not configured.", ephemeral=True)
            return
        
        embed = discord.Embed(title="Anti-Nuke Status", color=discord.Color.blue())
        embed.add_field(name="Enabled", value=str(settings['enabled']))
        embed.add_field(name="Alert Channel", value=f"<#{settings['alert_channel_id']}>" if settings['alert_channel_id'] else "Not set")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @antinuke_group.command(name="emergency", description="Toggle Emergency Mode")
    @app_commands.checks.has_permissions(administrator=True)
    async def emergency(self, interaction: discord.Interaction, enabled: bool):
        await self.db.update_settings(interaction.guild_id, emergency_mode=enabled)
        await interaction.response.send_message(f"Emergency mode set to {enabled}.", ephemeral=True)

    # Listeners
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        # Rollback: Save before deletion
        snapshot = await self.detector.actions.get_channel_snapshot(channel)
        await self.detector.handle_action(channel.guild, "CHANNEL_DELETE", channel)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.detector.handle_action(channel.guild, "CHANNEL_CREATE", channel)
        
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.detector.handle_action(guild, "BAN", user)

    # Add other listeners...
