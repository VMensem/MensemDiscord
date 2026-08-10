import discord

from .config import CONFIG
from .database import add_event_history, create_event
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
        self.date_input = discord.ui.TextInput(label="Дата (DD.MM.YYYY)", placeholder="10.08.2026", max_length=10)
        self.time_input = discord.ui.TextInput(label="Время (HH:MM)", placeholder="14:00", max_length=5)
        self.duration_input = discord.ui.TextInput(label="Длительность", placeholder="2 часа")
        self.participants_input = discord.ui.TextInput(label="Макс. участников", placeholder="20")
        self.reward_input = discord.ui.TextInput(label="Награда", placeholder="Нет / Золото", max_length=50)

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.date_input)
        self.add_item(self.time_input)
        self.add_item(self.duration_input)
        self.add_item(self.participants_input)
        self.add_item(self.reward_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or interaction.channel is None:
            await interaction.response.send_message("Команда работает только на сервере.", ephemeral=True)
            return

        title = str(self.title_input.value).strip()
        description = str(self.description_input.value).strip()
        date = str(self.date_input.value).strip()
        time = str(self.time_input.value).strip()
        duration = str(self.duration_input.value).strip()
        participants = int(self.participants_input.value)
        reward = str(self.reward_input.value).strip()

        embed = discord.Embed(title=title, description=description, color=CONFIG["EMBED_COLOR"])
        embed.add_field(name="Дата", value=f"{date} {time}", inline=True)
        embed.add_field(name="Длительность", value=duration, inline=True)
        embed.add_field(name="Макс. участников", value=participants, inline=True)
        embed.add_field(name="Награда", value=reward, inline=True)
        embed.add_field(name="Создатель", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Mensem Events System")
        embed.timestamp = discord.utils.utcnow()

        message = await interaction.channel.send(embed=embed)
        
        event_id = await create_event(
            interaction.guild.id,
            interaction.user.id,
            title,
            description,
            f"{date} {time}",
            duration,
            participants,
            reward,
            interaction.channel.id,
            message.id,
        )
        
        await add_event_history(event_id, "created", interaction.user.id, f"Created in #{interaction.channel.id}")
        await interaction.response.send_message(f"Событие создано: #{event_id}", ephemeral=True)


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
        await interaction.response.edit_message(view=None)
