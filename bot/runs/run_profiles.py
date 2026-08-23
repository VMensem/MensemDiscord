import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

async def main():
    async with bot:
        await bot.load_extension("profiles.bot")
        await bot.start(os.getenv("TOKEN"))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
