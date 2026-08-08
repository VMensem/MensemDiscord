from __future__ import annotations

import logging

import discord
from discord.ext import commands

from .config import WELCOME_CHANNEL_ID
from .generator import generate_welcome


logger = logging.getLogger(__name__)


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot or not WELCOME_CHANNEL_ID:
            return

        guild = member.guild
        channel = guild.get_channel(WELCOME_CHANNEL_ID)
        if channel is None:
            try:
                channel = await guild.fetch_channel(WELCOME_CHANNEL_ID)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                logger.warning("Welcome channel %s not available for guild %s", WELCOME_CHANNEL_ID, guild.id)
                return

        if channel is None or not hasattr(channel, "send"):
            return

        try:
            image = await generate_welcome(member)
        except Exception:
            logger.exception("Failed to generate welcome image for member %s", member.id)
            return

        embed = discord.Embed(
            title="Добро пожаловать!",
            description=(
                f"{member.mention}, рады видеть тебя на сервере.\n"
                "Посмотри правила и не забудь пройти верификацию."
            ),
            color=discord.Color.red(),
        )
        embed.set_image(url="attachment://welcome.png")
        embed.set_thumbnail(url=member.display_avatar.url)

        try:
            await channel.send(embed=embed, file=discord.File(image, filename="welcome.png"))
        except (discord.Forbidden, discord.HTTPException):
            logger.exception("Failed to send welcome message for member %s", member.id)


async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeCog(bot))
    print("OK Welcome module loaded")
