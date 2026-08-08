import os
import sqlite3
import time

import discord
from discord import app_commands
from discord.ext import commands


DB_PATH = "leveling/data/leveling.db"
XP_PER_MESSAGE = 15
COOLDOWN_SECONDS = 60


def init_db():
    os.makedirs("leveling/data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS levels (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                xp INTEGER NOT NULL DEFAULT 0,
                last_xp REAL NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
            """
        )


def level_for_xp(xp: int) -> int:
    return int((max(0, xp) / 100) ** 0.5)


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return

        now = time.time()
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT xp, last_xp FROM levels WHERE guild_id = ? AND user_id = ?",
                (message.guild.id, message.author.id),
            ).fetchone()
            old_xp = int(row[0]) if row else 0
            last_xp = float(row[1]) if row else 0
            if now - last_xp < COOLDOWN_SECONDS:
                return

            new_xp = old_xp + XP_PER_MESSAGE
            conn.execute(
                """
                INSERT INTO levels (guild_id, user_id, xp, last_xp)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id) DO UPDATE SET xp = excluded.xp, last_xp = excluded.last_xp
                """,
                (message.guild.id, message.author.id, new_xp, now),
            )
            conn.commit()

        if level_for_xp(new_xp) > level_for_xp(old_xp):
            channel_id = int(os.getenv("LEVEL_UP_CHANNEL_ID", 0) or 0)
            channel = message.guild.get_channel(channel_id) if channel_id else message.channel
            await channel.send(f"{message.author.mention}, новый уровень: {level_for_xp(new_xp)}")

    @app_commands.command(name="rank", description="Показать уровень участника")
    async def rank(self, interaction: discord.Interaction, member: discord.Member | None = None):
        if interaction.guild is None:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)
        target = member or interaction.user
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT xp FROM levels WHERE guild_id = ? AND user_id = ?",
                (interaction.guild.id, target.id),
            ).fetchone()
        xp = int(row[0]) if row else 0
        embed = discord.Embed(title=f"Уровень {target.display_name}", color=discord.Color.red())
        embed.add_field(name="Уровень", value=str(level_for_xp(xp)))
        embed.add_field(name="XP", value=str(xp))
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Leveling(bot))
