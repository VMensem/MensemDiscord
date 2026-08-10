from core.database import db_manager
import time

import discord
from discord import app_commands
from discord.ext import commands

XP_PER_MESSAGE = 15
COOLDOWN_SECONDS = 60

def level_for_xp(xp: int) -> int:
    return int((max(0, xp) / 100) ** 0.5)

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return

        now = time.time()
        
        row = await db_manager.fetchrow(
            "SELECT xp, last_xp FROM users WHERE guild_id = $1 AND user_id = $2",
            message.guild.id, message.author.id
        )
        
        old_xp = int(row["xp"]) if row else 0
        last_xp = float(row["last_xp"]) if row else 0
        if now - last_xp < COOLDOWN_SECONDS:
            return

        new_xp = old_xp + XP_PER_MESSAGE
        await db_manager.execute(
            """
            INSERT INTO users (guild_id, user_id, xp, last_xp)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (guild_id, user_id) DO UPDATE SET xp = excluded.xp, last_xp = excluded.last_xp
            """,
            message.guild.id, message.author.id, new_xp, now
        )

        if level_for_xp(new_xp) > level_for_xp(old_xp):
            pass

    @app_commands.command(name="rank", description="Показать уровень участника")
    async def rank(self, interaction: discord.Interaction, member: discord.Member | None = None):
        if interaction.guild is None:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)
        target = member or interaction.user
        row = await db_manager.fetchrow(
            "SELECT xp FROM users WHERE guild_id = $1 AND user_id = $2",
            interaction.guild.id, target.id
        )
        xp = int(row["xp"]) if row else 0
        embed = discord.Embed(title=f"Уровень {target.display_name}", color=discord.Color.red())
        embed.add_field(name="Уровень", value=str(level_for_xp(xp)))
        embed.add_field(name="XP", value=str(xp))
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
