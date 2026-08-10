import discord
from discord import app_commands
from discord.ext import commands
from .database import add_reaction_role, get_role_id

def emoji_key(emoji) -> str:
    return str(emoji)

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reaction-role", description="Привязать реакцию к роли")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reaction_role(
        self,
        interaction: discord.Interaction,
        message_id: str,
        emoji: str,
        role: discord.Role,
    ):
        if interaction.guild is None:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)
        if not message_id.isdigit():
            return await interaction.response.send_message("message_id должен быть числом.", ephemeral=True)

        await add_reaction_role(interaction.guild.id, int(message_id), emoji, role.id)

        try:
            message = await interaction.channel.fetch_message(int(message_id))
            await message.add_reaction(emoji)
        except discord.HTTPException:
            pass

        await interaction.response.send_message(
            f"Реакция {emoji} теперь выдаёт роль {role.mention}.",
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id is None or payload.member is None or payload.member.bot:
            return
        role_id = await get_role_id(payload.guild_id, payload.message_id, emoji_key(payload.emoji))
        if role_id is None:
            return
        role = payload.member.guild.get_role(role_id)
        if role is not None:
            await payload.member.add_roles(role, reason="Reaction role")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        role_id = await get_role_id(payload.guild_id, payload.message_id, emoji_key(payload.emoji))
        if role_id is None:
            return
        member = guild.get_member(payload.user_id)
        role = guild.get_role(role_id)
        if member is not None and role is not None:
            await member.remove_roles(role, reason="Reaction role removed")

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
