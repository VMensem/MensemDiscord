import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio
import logging
import subprocess

logger = logging.getLogger(__name__)

class VoiceTTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_ffmpeg_path(self):
        # Path provided by user
        return r"C:\hueta\ffmpeg\bin\ffmpeg.exe"

    def check_ffmpeg(self):
        path = self.get_ffmpeg_path()
        return os.path.exists(path)

    @commands.hybrid_command(name="voice_welcome", description="Голосовое приветствие")
    async def voice_welcome(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Вы должны находиться в голосовом канале!")
            return

        ffmpeg_path = self.get_ffmpeg_path()
        if not self.check_ffmpeg():
            logger.error(f"FFmpeg not found at {ffmpeg_path}!")
            await ctx.send("Ошибка: FFmpeg не найден по указанному пути.")
            return

        channel = ctx.author.voice.channel
        guild = ctx.guild
        voice_client = guild.voice_client

        try:
            if voice_client:
                if voice_client.channel != channel:
                    await voice_client.move_to(channel)
            else:
                logger.info(f"Attempting to connect to {channel.name}")
                voice_client = await channel.connect()
                logger.info(f"Connected to {channel.name}")

            text = os.getenv("VOICE_WELCOME_TEXT", "Доброго времени суток! Вы попали на сервер Mensem. Я ваш голосовой помощник. Если у вас есть вопросы, не стесняйтесь задавать их в чате.")
            tts = gTTS(text=text, lang='ru')
            filename = f"tts_{guild.id}.mp3"
            tts.save(filename)

            logger.info("Starting playback")
            # Using executable parameter to specify the path to ffmpeg
            source = discord.FFmpegPCMAudio(filename, executable=ffmpeg_path)
            voice_client.play(source, after=lambda e: logger.info(f"Playback finished: {e}"))
            
            while voice_client.is_playing():
                await asyncio.sleep(1)
            
            await asyncio.sleep(2) 
        except Exception as e:
            logger.exception(f"TTS/Voice error: {e}")
            await ctx.send("Произошла ошибка при воспроизведении голосового приветствия.")
        finally:
            if voice_client and voice_client.is_connected():
                await voice_client.disconnect()
                logger.info("Disconnected")
            if os.path.exists(filename):
                os.remove(filename)

async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceTTS(bot))
