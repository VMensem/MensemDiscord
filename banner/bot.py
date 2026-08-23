from __future__ import annotations

import os
import logging

import discord
from discord.ext import commands, tasks

from . import cache, config, generator, stats, updater


logger = logging.getLogger(__name__)
# Set level based on DEBUG_MODE (defaulting to WARNING if not true)
debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
logger.setLevel(logging.DEBUG if debug_mode else logging.WARNING)


class BannerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache = cache.BannerCache()
        self._chunked_guilds = False

    def cog_unload(self):
        if self.banner_loop.is_running():
            self.banner_loop.cancel()

    async def _chunk_guilds_once(self) -> None:
        if self._chunked_guilds:
            return
        self._chunked_guilds = True
        for guild in self.bot.guilds:
            try:
                await guild.chunk()
            except (discord.Forbidden, discord.HTTPException):
                logger.debug("Skipping chunk for guild %s", guild.id, exc_info=True)

    @tasks.loop(seconds=config.BANNER_UPDATE_INTERVAL_SECONDS)
    async def banner_loop(self):
        if not config.BANNER_ENABLED:
            return

        await self._chunk_guilds_once()

        for guild in self.bot.guilds:
            try:
                current_stats = await stats.get_guild_stats(guild)
                if not self.cache.has_changed(current_stats):
                    continue

                logger.info("Banner update triggered for %s", guild.name)
                image_path = generator.generate_banner(current_stats)
                updated = await updater.update_banner(guild, image_path)
                if updated:
                    logger.info("Banner updated for guild %s", guild.id)
            except Exception:
                logger.exception("Banner update failed for guild %s", guild.id)

    @commands.Cog.listener()
    async def on_ready(self):
        if not config.BANNER_ENABLED or self.banner_loop.is_running():
            return
        self.banner_loop.start()

    @banner_loop.before_loop
    async def before_banner_loop(self):
        try:
            await self.bot.wait_until_ready()
            await self._chunk_guilds_once()
        except Exception:
            logger.exception("Banner loop failed during startup")
            if self.banner_loop.is_running():
                self.banner_loop.cancel()


async def setup(bot: commands.Bot):
    await bot.add_cog(BannerCog(bot))
