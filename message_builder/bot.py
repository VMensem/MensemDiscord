import logging
import os

import discord
from aiohttp import web
from discord import app_commands
from discord.ext import commands

def _candidate_ports() -> list[int]:
    web_port = int(os.getenv("WEB_PORT", 5000))
    raw_port = os.getenv("MESSAGE_BUILDER_PORT") or os.getenv("BOT_INTERNAL_PORT")
    candidates: list[int] = []

    try:
        preferred = int(raw_port) if raw_port else 8081
    except ValueError:
        preferred = 8081

    for port in (preferred, 8081, 8082, 8083, 8084):
        if port == web_port or port in candidates:
            continue
        candidates.append(port)

    return candidates


class MessageBuilderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.app.router.add_post("/api/send-message", self.handle_send)
        self.runner = web.AppRunner(self.app)
        self.site = None

    async def cog_load(self):
        await self.runner.setup()
        last_error: OSError | None = None

        for port in _candidate_ports():
            self.site = web.TCPSite(self.runner, "localhost", port)
            try:
                await self.site.start()
                return
            except OSError as exc:
                last_error = exc
                self.site = None

        if last_error is not None:
            logging.warning("Message builder internal API disabled: %s", last_error)
            await self.runner.cleanup()

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
