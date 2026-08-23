import discord
from discord.ui import View, Select, Button, Modal, TextInput
from core.database import db_manager

class ClanSettingsModal(Modal, title="Настройки клана"):
    name = TextInput(label="Новое название", required=False)
    tag = TextInput(label="Новый тег", min_length=2, max_length=4, required=False)
    description = TextInput(label="Описание", style=discord.TextStyle.paragraph, max_length=200, required=False)

    def __init__(self, clan_id):
        super().__init__()
        self.clan_id = clan_id

    async def on_submit(self, interaction: discord.Interaction):
        updates = {}
        if self.name.value: updates["name"] = self.name.value
        if self.tag.value: updates["tag"] = self.tag.value
        if self.description.value: updates["description"] = self.description.value
        
        if updates:
            fields = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(updates.keys())])
            values = list(updates.values())
            await db_manager.execute(
                f"UPDATE clans SET {fields} WHERE clan_id = $1",
                self.clan_id, *values
            )
            await interaction.response.send_message("Настройки обновлены!", ephemeral=True)
        else:
            await interaction.response.send_message("Ничего не изменено.", ephemeral=True)

class ClanSettingsView(View):
    def __init__(self, clan_id):
        super().__init__(timeout=60)
        self.clan_id = clan_id

    @discord.ui.select(
        placeholder="Выберите настройку",
        options=[
            discord.SelectOption(label="📝 Изменить информацию", value="info"),
            discord.SelectOption(label="🎨 Цвет роли", value="color"),
        ]
    )
    async def select_settings(self, interaction: discord.Interaction, select: Select):
        if select.values[0] == "info":
            await interaction.response.send_modal(ClanSettingsModal(self.clan_id))
        else:
            await interaction.response.send_message("Настройка цвета в разработке.", ephemeral=True)
