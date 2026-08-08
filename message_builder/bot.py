import logging
import os

import discord
from aiohttp import web
from discord import app_commands
from discord.ext import commands

from .database import init_db


class MessageBuilderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()
        self.app = web.Application()
        self.app.router.add_post("/api/send-message", self.handle_send)
        self.runner = web.AppRunner(self.app)
        self.site = None

    async def cog_load(self):
        await self.runner.setup()
        web_port = int(os.getenv("WEB_PORT", 5000))
        raw_port = os.getenv("MESSAGE_BUILDER_PORT") or os.getenv("BOT_INTERNAL_PORT")
        try:
            port = int(raw_port) if raw_port else 8081
        except ValueError:
            port = 8081
        if port == web_port:
            port = 8081 if web_port != 8081 else 8082

        self.site = web.TCPSite(self.runner, "localhost", port)
        try:
            await self.site.start()
        except OSError as exc:
            logging.warning("Message builder internal API disabled on port %s: %s", port, exc)
            await self.runner.cleanup()
            self.site = None

    async def cog_unload(self):
        if self.site is not None:
            await self.runner.cleanup()

    async def handle_send(self, request):
        token = request.headers.get("Authorization")
        if token != os.getenv("MESSAGE_BUILDER_TOKEN"):
            return web.Response(status=401)

        data = await request.json()
        channel = self.bot.get_channel(int(data["channel_id"]))
        if not channel:
            return web.json_response({"error": "Channel not found"}, status=404)

        embed_data = data.get("embed")
        embed = discord.Embed.from_dict(embed_data) if embed_data else None

        await channel.send(content=data.get("content"), embed=embed)
        return web.json_response({"status": "ok"})

    @app_commands.command(name="message", description="Конструктор сообщений")
    async def message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Message Builder",
            description="Используйте веб-конструктор для создания сообщений:",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Веб-конструктор", value="http://localhost:5000/embeds")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(MessageBuilderCog(bot))
