import discord
from discord.ui import View, Select, Button, Modal, TextInput

class ClanSettingsModal(Modal, title="Настройки клана"):
    name = TextInput(label="Название", placeholder="Введите новое название")
    description = TextInput(label="Описание", placeholder="Введите новое описание", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Настройки обновлены!", ephemeral=True)

class ClanManageView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Управление кланом",
        custom_id="clan_manage_select",
        options=[
            discord.SelectOption(label="👥 Участники", value="members"),
            discord.SelectOption(label="⚙️ Настройки", value="settings"),
        ]
    )
    async def manage_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "settings":
            await interaction.response.send_modal(ClanSettingsModal())
        else:
            await interaction.response.send_message(f"Выбрано: {select.values[0]}", ephemeral=True)
