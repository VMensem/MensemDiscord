import asyncio
import logging
import random
from datetime import datetime, timezone

import discord

from .database import get_all_giveaways, finish_giveaway, get_participants


RED = discord.Color.from_rgb(220, 20, 60)


class GiveawayManager:
    def __init__(self, bot):
        self.bot = bot

    async def start(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            giveaways = await get_all_giveaways()

            for giveaway in giveaways:
                if giveaway["ended"]:
                    continue

                end_time = giveaway["end_time"]
                
                # Ensure end_time is timezone aware for comparison
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)

                if datetime.now(timezone.utc) >= end_time:
                    await self.finish(giveaway)

            await asyncio.sleep(15)

    async def finish(self, giveaway):
        message_id = giveaway["message_id"]
        channel_id = giveaway["channel_id"]

        channel = self.bot.get_channel(channel_id)
        if not channel:
            await finish_giveaway(message_id)
            return

        try:
            message = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            await finish_giveaway(message_id)
            return
        except Exception:
            logging.exception("Unexpected giveaway fetch error")
            await finish_giveaway(message_id)
            return

        participants = await get_participants(message_id)

        embed = discord.Embed(
            title="🎉 Розыгрыш завершён",
            color=RED,
        )
        embed.add_field(name="🎁 Приз", value=f"**{giveaway['prize']}**", inline=False)

        winner = None
        if participants:
            winner = random.choice(participants)
            embed.add_field(name="🏆 Победитель", value=f"<@{winner}>", inline=False)
        else:
            embed.add_field(name="🏆 Победитель", value="Нет участников 😢", inline=False)

        embed.add_field(name="👥 Участников", value=str(len(participants)), inline=True)
        embed.set_footer(text="Спасибо всем за участие ❤️")

        await message.edit(embed=embed, view=None)

        if winner:
            await channel.send(f"🎉 Поздравляем <@{winner}>! Ты выиграл **{giveaway['prize']}** 🏆")
        else:
            await channel.send("😢 Розыгрыш завершён, но участников не было.")

        await finish_giveaway(message_id)
