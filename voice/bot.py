import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from voice.database import init_database
from voice.loader import load_modules


load_dotenv()


def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True
    intents.voice_states = True

    bot = commands.Bot(
        command_prefix="!",
        intents=intents,
        help_command=None,
    )

    @bot.event
    async def on_ready():
        print("=" * 50)
        print(f"OK {bot.user} started")
        print(f"Guilds: {len(bot.guilds)}")
        print("=" * 50)

    load_modules(bot)
    return bot


def run():
    token = os.getenv("TOKEN")
    if not token:
        raise RuntimeError("TOKEN not found in .env")

    bot = create_bot()
    bot.run(token)


async def setup(bot: commands.Bot):
    await init_database()
    load_modules(bot)
    print("OK Voice module loaded as extension")
