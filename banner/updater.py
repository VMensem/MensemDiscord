from __future__ import annotations

import logging

import discord

from . import config


async def update_banner(guild: discord.Guild, image_path: str) -> bool:
    try:
        with open(image_path, "rb") as file:
            banner_bytes = file.read()
    except OSError:
        logging.exception("Failed to open generated banner image: %s", image_path)
        return False

    if config.BANNER_DEPLOY_MODE:
        try:
            await guild.edit(banner=banner_bytes)
            return True
        except discord.Forbidden:
            logging.warning("Missing permission to edit banner for guild %s", guild.id)
        except discord.HTTPException:
            logging.exception("Discord rejected banner update for guild %s", guild.id)
        return False

    if config.BANNER_DEBUG_MODE:
        channel = guild.get_channel(config.BANNER_DEBUG_CHANNEL_ID)
        if channel is None:
            try:
                channel = await guild.fetch_channel(config.BANNER_DEBUG_CHANNEL_ID)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                channel = None
        if channel is None or not hasattr(channel, "send"):
            logging.warning("Banner debug channel not available for guild %s", guild.id)
            return False

        try:
            await channel.send(file=discord.File(image_path))
            return True
        except (discord.Forbidden, discord.HTTPException):
            logging.exception("Failed to send debug banner for guild %s", guild.id)
        return False

    return False
