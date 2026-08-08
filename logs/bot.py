from discord.ext import commands

from .channels import setup_channels
from .events import setup_events
from .guild import setup_guild
from .messages import setup_messages
from .moderation import setup_moderation
from .roles import setup_roles
from .voice import setup_voice


async def setup(bot: commands.Bot):
    setup_events(bot)
    setup_messages(bot)
    setup_roles(bot)
    setup_voice(bot)
    setup_guild(bot)
    setup_channels(bot)
    setup_moderation(bot)
    print("OK Logs module loaded")
