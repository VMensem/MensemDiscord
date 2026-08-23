import logging
import asyncio
import discord
from discord.ext import commands, tasks

logger = logging.getLogger(__name__)

CHANNEL_ID = 1524068137090289707

class VoicePresence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_ready = False
        logger.info("[VOICE PRESENCE] Module loaded")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.is_ready:
            self.is_ready = True
            logger.info("[VOICE PRESENCE] Discord ready")
            self.presence_task.start()

    def cog_unload(self):
        logger.info("[VOICE PRESENCE] Stopping")
        self.presence_task.cancel()
        for vc in self.bot.voice_clients:
            if vc.channel and vc.channel.id == CHANNEL_ID:
                asyncio.create_task(vc.disconnect())

    @tasks.loop(seconds=60)
    async def presence_task(self):
        if self.bot.is_closed():
            self.presence_task.stop()
            return

        channel = self.bot.get_channel(CHANNEL_ID)
        if not channel or not isinstance(channel, discord.VoiceChannel):
            logger.warning(f"[VOICE PRESENCE] Voice channel not found: {CHANNEL_ID}")
            return

        # Check existing connections
        vc = discord.utils.get(self.bot.voice_clients, guild=channel.guild)
        
        if vc and vc.is_connected():
            if vc.channel and vc.channel.id == CHANNEL_ID:
                return # Already connected
            else:
                logger.info(f"[VOICE PRESENCE] Reconnecting to channel {CHANNEL_ID}...")
                await vc.move_to(channel)
                return

        try:
            logger.info(f"[VOICE PRESENCE] Connecting to channel {CHANNEL_ID}")
            await channel.connect()
            logger.info("[VOICE PRESENCE] Connected successfully")
        except discord.Forbidden:
            logger.error("[VOICE PRESENCE] Missing permissions to connect")
        except Exception as e:
            logger.error(f"[VOICE PRESENCE] Connection error: {e}")

    @presence_task.before_loop
    async def before_presence(self):
        logger.info("[VOICE PRESENCE] Waiting for Discord ready")
        # Loop will only start after on_ready sets is_ready=True
        while not self.is_ready:
            await asyncio.sleep(1)

async def setup(bot):
    await bot.add_cog(VoicePresence(bot))
    logger.info("[VOICE PRESENCE] Module loaded")
