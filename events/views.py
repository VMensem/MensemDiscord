import discord

from .config import CONFIG
from .api_client import api_client
from .embeds import create_event_menu_embed


class CreateEventModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Создать событие")
        self.title_input = discord.ui.TextInput(label="Название", max_length=80)
        self.description_input = discord.ui.TextInput(
            label="Описание",
            style=discord.TextStyle.paragraph,
            max_length=1200,
        )
        self.datetime_input = discord.ui.TextInput(
            label="Дата и время (DD.MM.YYYY HH:MM)", 
            placeholder="10.08.2026 14:00", 
            max_length=16
        )
        self.details_input = discord.ui.TextInput(
            label="Длительность, Макс. участников, Награда",
            placeholder="2 часа, 20, Золото",
            max_length=100
        )
        # Оставляем 4 компонента вместо 7

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.datetime_input)
        self.add_item(self.details_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or interaction.channel is None:
            await interaction.response.send_message("Команда работает только на сервере.", ephemeral=True)
            return

        title = str(self.title_input.value).strip()
        description = str(self.description_input.value).strip()
        
        # Парсинг объединённых полей
        dt_parts = str(self.datetime_input.value).strip().split(" ")
        date = dt_parts[0] if len(dt_parts) > 0 else ""
        time = dt_parts[1] if len(dt_parts) > 1 else ""
        
        det_parts = str(self.details_input.value).strip().split(",")
        duration = det_parts[0].strip() if len(det_parts) > 0 else "Не указано"
        participants = int(det_parts[1].strip()) if len(det_parts) > 1 and det_parts[1].strip().isdigit() else 0
        reward = det_parts[2].strip() if len(det_parts) > 2 else "Нет"


        embed = discord.Embed(title=title, description=description, color=CONFIG["EMBED_COLOR"])
        embed.add_field(name="Дата", value=f"{date} {time}", inline=True)
        embed.add_field(name="Длительность", value=duration, inline=True)
        embed.add_field(name="Макс. участников", value=participants, inline=True)
        embed.add_field(name="Награда", value=reward, inline=True)
        embed.add_field(name="Создатель", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Mensem Events System")
        embed.timestamp = discord.utils.utcnow()

        message = await interaction.channel.send(embed=embed)
        
        result = await api_client.create_event({
            "guild_id": interaction.guild.id,
            "creator_id": interaction.user.id,
            "title": title,
            "description": description,
            "start_time": f"{date} {time}",
            "duration": duration,
            "max_participants": participants,
            "reward": reward,
            "channel_id": interaction.channel.id,
            "message_id": message.id,
        })
        
        if result and result.get("data") and result["data"].get("event_id"):
            event_id = result["data"]["event_id"]
            await interaction.response.send_message(f"Событие создано через API: #{event_id}", ephemeral=True)
        else:
            await interaction.response.send_message("Ошибка при создании события через API.", ephemeral=True)



class CloseEventModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Закрыть событие")
        self.event_id_input = discord.ui.TextInput(label="ID события", placeholder="Введите ID события для закрытия")
        self.add_item(self.event_id_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        event_id = str(self.event_id_input.value).strip()
        if not event_id.isdigit():
            await interaction.response.send_message("ID должен быть числом.", ephemeral=True)
            return
            
        result = await api_client.close_event(int(event_id), interaction.guild.id)
        if result and result.get("status") == 200:
            await interaction.response.send_message(f"Событие #{event_id} успешно закрыто.", ephemeral=True)
        else:
            error = result.get("error", "Неизвестная ошибка")
            await interaction.response.send_message(f"Ошибка при закрытии события: {error}", ephemeral=True)

class MainEventMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Создать",
        emoji="➕",
        style=discord.ButtonStyle.success,
        custom_id="evt_create",
    )
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreateEventModal())

    @discord.ui.button(
        label="Обновить",
        emoji="🔄",
        style=discord.ButtonStyle.secondary,
        custom_id="evt_refresh",
    )
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message("Команда работает только на сервере.", ephemeral=True)
            return
        embed = await create_event_menu_embed(interaction.guild, interaction.user)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Закрыть",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        custom_id="evt_close",
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message("Команда работает только на сервере.", ephemeral=True)
            return
        
        await interaction.response.send_modal(CloseEventModal())

