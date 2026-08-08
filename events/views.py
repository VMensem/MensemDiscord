import discord

from .config import CONFIG
from .database import add_event_history, create_event
from .embeds import create_event_menu_embed


class CreateEventModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Создать событие")
        self.title_input = discord.ui.TextInput(label="Название", max_length=80)
        self.type_input = discord.ui.TextInput(
            label="Тип события",
            placeholder="Например: movie / game / chat",
            max_length=32,
        )
        self.description_input = discord.ui.TextInput(
            label="Описание",
            style=discord.TextStyle.paragraph,
            max_length=1200,
        )
        self.add_item(self.title_input)
        self.add_item(self.type_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or interaction.channel is None:
            await interaction.response.send_message("Команда работает только на сервере.", ephemeral=True)
            return

        title = str(self.title_input.value).strip()
        event_type = str(self.type_input.value).strip()
        description = str(self.description_input.value).strip()

        if not title or not event_type or not description:
            await interaction.response.send_message("Заполни все поля.", ephemeral=True)
            return

        embed = discord.Embed(title=title, description=description, color=CONFIG["EMBED_COLOR"])
        embed.add_field(name="Тип", value=event_type, inline=True)
        embed.add_field(name="Создатель", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Mensem Events System")
        embed.timestamp = discord.utils.utcnow()

        message = await interaction.channel.send(embed=embed)
        event_id = create_event(
            interaction.guild.id,
            interaction.user.id,
            title,
            event_type,
            interaction.channel.id,
            message.id,
            {"description": description},
        )
        add_event_history(event_id, "created", interaction.user.id, f"Created in #{interaction.channel.id}")
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
        embed = create_event_menu_embed(interaction.guild, interaction.user)
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
