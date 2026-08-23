import discord

from .config import CONFIG
from .database import create_report


class ReportPanelButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Создать репорт", style=discord.ButtonStyle.danger, custom_id="rep_create_btn")
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReportModal())


class ReportModal(discord.ui.Modal, title="Создание жалобы"):
    reason = discord.ui.TextInput(label="Причина жалобы", style=discord.TextStyle.short)
    desc = discord.ui.TextInput(label="Описание", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        report_id = await create_report(
            interaction.guild_id,
            interaction.user.id,
            interaction.channel.id if interaction.channel else 0,
            str(self.reason.value),
            str(self.desc.value),
        )
        embed = discord.Embed(
            title=f"Репорт R-{report_id:04d}",
            description=str(self.desc.value),
            color=discord.Color.red(),
        )
        embed.add_field(name="Автор", value=interaction.user.mention, inline=False)
        embed.add_field(name="Причина", value=str(self.reason.value), inline=False)

        log_channel = interaction.guild.get_channel(CONFIG["LOG_CHANNEL"]) if interaction.guild and CONFIG["LOG_CHANNEL"] else None
        if log_channel:
            await log_channel.send(embed=embed, view=TicketControlView())

        await interaction.response.send_message(f"Репорт R-{report_id:04d} создан.", ephemeral=True)


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary, custom_id="rep_claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"Репорт взял в работу {interaction.user.mention}.")
