import asyncio
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from setup_configurator.main import run_setup

load_dotenv()
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    if not GUILD_ID:
        print("Error: GUILD_ID not found in .env file.")
        await bot.close()
        return

    guild = bot.get_guild(GUILD_ID)
    if guild:
        print(f"Running setup for guild: {guild.name}")
        await run_setup(guild)
    else:
        print(f"Bot is not in the guild with ID: {GUILD_ID}")
    
    await bot.close()

if __name__ == "__main__":
    if not TOKEN:
        print("Error: TOKEN not found in .env file.")
    else:
        bot.run(TOKEN)
