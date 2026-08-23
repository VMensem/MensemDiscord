import asyncio
import logging
import random
from datetime import datetime, timezone

import discord

from .database import get_all_giveaways, finish_giveaway, get_participants, add_winner


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
        winner_count = giveaway["winner_count"]

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
        embed.add_field(name="🏆 Победителей", value=str(winner_count), inline=True)
        embed.add_field(name="👥 Участников", value=str(len(participants)), inline=True)
        if giveaway["conditions"]:
            embed.add_field(name="📋 Условия", value=giveaway["conditions"], inline=False)

        winners = []
        if participants:
            # Pick unique winners
            count = min(len(participants), winner_count)
            winners = random.sample(participants, count)
            
            # Save winners to DB
            for i, winner_id in enumerate(winners):
                await add_winner(message_id, winner_id, i+1)
            
            winner_mentions = "\n".join([f"<@{w}>" for w in winners])
            embed.add_field(name="🏆 Победители", value=winner_mentions, inline=False)
        else:
            embed.add_field(name="🏆 Победители", value="Нет участников 😢", inline=False)

        embed.set_footer(text="Спасибо всем за участие ❤️")
        
        # Add warning about manual condition check
        embed.add_field(name="⚠️ Внимание", value="Условия проверяются STAFF вручную.", inline=False)

        await message.edit(embed=embed, view=None)

        if winners:
            await channel.send(f"🎉 Поздравляем победителей! 🏆\n" + "\n".join([f"<@{w}>" for w in winners]))
        else:
            await channel.send("😢 Розыгрыш завершён, но участников не было.")

        await finish_giveaway(message_id)

