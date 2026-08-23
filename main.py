import asyncio
import logging
import os
import sys
import threading

from dotenv import load_dotenv

# Load .env from parent directory before importing modules that depend on it
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

import discord
from discord.ext import commands

import loader
from web_site.app import create_app
from core.database import db_manager


logging.basicConfig(level=logging.INFO)


TOKEN = os.getenv("TOKEN")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
COMMAND_GUILD_ID_RAW = os.getenv("GUILD_ID", "").strip()
COMMAND_GUILD_ID = int(COMMAND_GUILD_ID_RAW) if COMMAND_GUILD_ID_RAW.isdigit() else None


def get_env_int(key: str, default: int) -> int:
    raw = os.getenv(key, "").strip()
    return int(raw) if raw.isdigit() else default

# На Render ВСЕГДА нужно биндиться к 0.0.0.0
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = get_env_int("PORT", get_env_int("WEB_PORT", 5000))

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True
intents.presences = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
_synced_once = False


def safe_print(message: str):
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        sys.stdout.buffer.write((message + "\n").encode(encoding, errors="replace"))
        sys.stdout.flush()


def run_web_server():
    try:
        app = create_app()
        app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)
    except Exception as e:
        logging.error("Web server startup failed: %s", e)


def command_leaf_count(commands_):
    total = 0
    for command in commands_:
        children = getattr(command, "commands", None)
        total += len(children) if children else 1
    return total


def command_names(commands_):
    names = []
    for command in commands_:
        children = getattr(command, "commands", None)
        if children:
            names.extend(f"{command.name} {child.name}" for child in children)
        else:
            names.append(command.name)
    return names


@bot.event
async def on_ready():
    global _synced_once

    activity = discord.Activity(type=discord.ActivityType.playing, name="discord.gg/mensem")
    await bot.change_presence(activity=activity)
    safe_print(f"OK Activity set to: Playing {activity.name}")
    safe_print(f"OK Bot logged in as {bot.user}")

    if _synced_once:
        return
    _synced_once = True

    local_commands = bot.tree.get_commands()
    safe_print(
        f"Local slash tree: {len(local_commands)} top-level, "
        f"{command_leaf_count(local_commands)} executable commands"
    )
    for name in command_names(local_commands):
        safe_print(f"  - {name}")

    try:
        if COMMAND_GUILD_ID:
            guild = discord.Object(id=COMMAND_GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced_commands = await bot.tree.sync(guild=guild)
            fetched_commands = await bot.tree.fetch_commands(guild=guild)
            safe_print(
                f"OK Synced {len(synced_commands)} top-level slash commands "
                f"({command_leaf_count(local_commands)} executable) to guild {COMMAND_GUILD_ID}"
            )
            safe_print(
                f"OK Discord now has {len(fetched_commands)} top-level slash commands "
                f"for guild {COMMAND_GUILD_ID}"
            )
        else:
            synced_commands = await bot.tree.sync()
            fetched_commands = await bot.tree.fetch_commands()
            safe_print(
                f"OK Synced {len(synced_commands)} global top-level slash commands "
                f"({command_leaf_count(local_commands)} executable)"
            )
            safe_print(f"OK Discord now has {len(fetched_commands)} global top-level slash commands")
    except Exception:
        logging.exception("Failed to sync slash commands")
        safe_print("FAIL Failed to sync slash commands; see traceback above")
        await bot.close()
        return

    if DEBUG_MODE:
        safe_print("=" * 30)
        safe_print("MensemBot Starting")
        safe_print(f"Python version: {os.sys.version}")
        safe_print(f"Discord.py version: {discord.__version__}")
        safe_print(f"Web server running on http://{WEB_HOST}:{WEB_PORT}")
        safe_print("=" * 30)


@bot.event
async def on_command_error(ctx, error):
    logging.error("Command error: %s", error)


async def run_bot():
    await db_manager.connect()
    await loader.load_modules(bot)

    if not TOKEN:
        safe_print("FAIL TOKEN not found in .env")
        return

    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    await asyncio.sleep(1)
    
    if web_thread.is_alive():
        safe_print(f"OK Web server started in background: http://{WEB_HOST}:{WEB_PORT}")
    else:
        safe_print("FAIL Web server failed to start.")

    try:
        await bot.start(TOKEN)
    except asyncio.CancelledError:
        safe_print("Bot shutting down gracefully...")
    finally:
        await db_manager.close()
        await bot.close()


if __name__ == "__main__":
    asyncio.run(run_bot())
