import discord
from discord import ui

from .database import create_giveaway
from datetime import datetime, timedelta, timezone

class GiveawayModal(ui.Modal, title="Создание розыгрыша"):
    prize = ui.TextInput(label="Приз", style=discord.TextStyle.short, placeholder="Например: 5x Discord Nitro", required=True)
    duration = ui.TextInput(label="Длительность (например: 10s, 5m, 2h, 1d)", style=discord.TextStyle.short, placeholder="24h", required=True)
    winner_count = ui.TextInput(label="Количество победителей", style=discord.TextStyle.short, placeholder="1", required=True, default="1")
    conditions = ui.TextInput(label="Условия", style=discord.TextStyle.paragraph, placeholder="Подписка на канал...", required=True)
    image_url = ui.TextInput(label="Image URL (опционально)", style=discord.TextStyle.short, placeholder="https://...", required=False)

    def parse_duration(self, value: str):
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

    async def on_submit(self, interaction: discord.Interaction):
        time = self.parse_duration(self.duration.value)
        if not time:
            await interaction.response.send_message("❌ Неверный формат времени.\nПример: `30m`, `2h`, `1d`", ephemeral=True)
            return
        
        try:
            winners = int(self.winner_count.value)
            if winners < 1:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Количество победителей должно быть целым числом больше 0.", ephemeral=True)
            return

        await interaction.response.defer()
        
        end_time = datetime.now(timezone.utc) + time
        
        embed = discord.Embed(
            title="🎉 Розыгрыш",
            description=f"""
🎁 **Приз**
{self.prize.value}

🏆 **Победителей**
{winners}

📋 **Условия**
{self.conditions.value}

⏳ **Завершение**
<t:{int(end_time.timestamp())}:R>

👥 **Участников**
0
""",
            color=discord.Color.from_rgb(220, 20, 60)
        )
        
        if self.image_url.value:
            embed.set_image(url=self.image_url.value)
            
        embed.set_footer(
            text=f"Создал {interaction.user}",
            icon_url=interaction.user.display_avatar.url
        )
        
        message = await interaction.channel.send(embed=embed)
        
        from .views import GiveawayView
        await message.edit(view=GiveawayView(message.id))
        
        await create_giveaway(
            message_id=message.id,
            channel_id=interaction.channel.id,
            guild_id=interaction.guild.id,
            prize=self.prize.value,
            winner_count=winners,
            conditions=self.conditions.value,
            end_time=end_time.isoformat(),
            creator=interaction.user.id
        )
        
        await interaction.followup.send("✅ Розыгрыш создан!", ephemeral=True)
