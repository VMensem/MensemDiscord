# giveaways/cog.py

import discord
from discord.ext import commands
from discord import app_commands

from datetime import datetime, timedelta, timezone

from .views import GiveawayView
from .database import create_giveaway


RED = discord.Color.from_rgb(220, 20, 60)



def parse_duration(value: str):

    value = value.lower().strip()


    try:

        number = int(value[:-1])
        unit = value[-1]


    except (ValueError, IndexError):

        return None



    if unit == "s":

        return timedelta(seconds=number)


    elif unit == "m":

        return timedelta(minutes=number)


    elif unit == "h":

        return timedelta(hours=number)


    elif unit == "d":

        return timedelta(days=number)


    return None





class Giveaways(commands.Cog):


    def __init__(self, bot):

        self.bot = bot



    @app_commands.command(
        name="giveaway",
        description="Создать новый розыгрыш"
    )
    @app_commands.describe(
        prize="Приз",
        duration="Время (10s, 5m, 2h, 1d)",
        image_url="Картинка"
    )
    async def giveaway(
        self,
        interaction: discord.Interaction,
        prize: str,
        duration: str,
        image_url: str = None
    ):


        if not interaction.user.guild_permissions.manage_guild:

            await interaction.response.send_message(
                "❌ Недостаточно прав.",
                ephemeral=True
            )

            return



        time = parse_duration(duration)


        if not time:

            await interaction.response.send_message(
                "❌ Неверный формат времени.\nПример: `30m`, `2h`, `1d`",
                ephemeral=True
            )

            return



        await interaction.response.defer()



        end_time = (
            datetime.now(timezone.utc)
            +
            time
        )



        embed = discord.Embed(
            title="🎉 Розыгрыш",
            description=f"""
🎁 **Приз**
{prize}

⏳ **Завершение**
<t:{int(end_time.timestamp())}:R>

👥 **Участников**
0
""",
            color=RED
        )


        # Картинка справа
        if image_url:

            embed.set_thumbnail(
                url=image_url
            )


        embed.set_footer(
            text=f"Создал {interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )



        message = await interaction.channel.send(
            embed=embed
        )



        await message.edit(
            view=GiveawayView(
                message.id
            )
        )



        await create_giveaway(
            message_id=message.id,
            channel_id=interaction.channel.id,
            guild_id=interaction.guild.id,
            prize=prize,
            end_time=end_time.isoformat(),
            creator=interaction.user.id
        )



        await interaction.followup.send(
            "✅ Розыгрыш создан!",
            ephemeral=True
        )




async def setup(bot):

    await bot.add_cog(
        Giveaways(bot)
    )
