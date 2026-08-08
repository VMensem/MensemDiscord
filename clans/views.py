import discord

class ClanManageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Управление кланом",
        custom_id="clan_manage_select",
        options=[
            discord.SelectOption(label="👥 Участники", value="members"),
            discord.SelectOption(label="⭐ Роли", value="roles"),
            discord.SelectOption(label="👑 Лидерство", value="leader"),
            discord.SelectOption(label="⚙️ Настройки", value="settings"),
        ]
    )
    async def manage_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.send_message(f"Выбрано: {select.values[0]}", ephemeral=True)
