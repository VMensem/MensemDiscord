import discord
from discord.ui import View, Select, Modal, TextInput
from ..database import get_clans_by_guild # Need to fetch clan for user

class ClanSettingsModal(Modal, title="Настройки клана"):
    name = TextInput(label="Название", placeholder="Введите новое название")
    description = TextInput(label="Описание", placeholder="Введите новое описание", style=discord.TextStyle.paragraph)

    def __init__(self, clan_id):
        super().__init__()
        self.clan_id = clan_id

    async def on_submit(self, interaction: discord.Interaction):
        from core.database import db_manager # Need inside to avoid circular
        await db_manager.execute(
            "UPDATE clans SET name = $1, description = $2 WHERE clan_id = $3",
            self.name.value, self.description.value, self.clan_id
        )
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
        # Dynamically fetch clan_id for user
        from core.database import db_manager
        row = await db_manager.fetchrow("SELECT clan_id FROM clan_members WHERE user_id = $1", interaction.user.id)
        if not row:
            return await interaction.response.send_message("Вы не состоите в клане.", ephemeral=True)
        clan_id = row["clan_id"]

        if select.values[0] == "settings":
            await interaction.response.send_modal(ClanSettingsModal(clan_id))
        else:
            await interaction.response.send_message(f"Управление участниками для клана {clan_id} (в разработке).", ephemeral=True)
