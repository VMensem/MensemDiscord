import asyncio
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables (assuming .env exists in project root)
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Setup bot
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Load the extension
    await bot.load_extension("server_management.bot")
    print("server_management cog loaded.")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: TOKEN not found in .env file.")
    else:
        bot.run(TOKEN)
