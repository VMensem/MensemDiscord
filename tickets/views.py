import os

import discord

from .database import close_ticket, create_ticket


def ticket_category_id() -> int:
    raw = os.getenv("TICKET_CATEGORY_ID", "0").strip()
    return int(raw) if raw.isdigit() else 0


def ticket_log_channel_id() -> int:
    raw = os.getenv("TICKET_LOG_CHANNEL_ID", "0").strip()
    return int(raw) if raw.isdigit() else 0


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Создать тикет", style=discord.ButtonStyle.primary, custom_id="ticket_create")
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("Тикеты доступны только на сервере.", ephemeral=True)

        category = guild.get_channel(ticket_category_id()) if ticket_category_id() else None
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        name = f"ticket-{interaction.user.name}".lower().replace(" ", "-")[:90]
        try:
            channel = await guild.create_text_channel(name=name, category=category, overwrites=overwrites)
        except discord.Forbidden:
            return await interaction.response.send_message("У бота нет прав на создание тикетов.", ephemeral=True)

        ticket_id = create_ticket(guild.id, interaction.user.id, channel.id)
        embed = discord.Embed(
            title=f"Тикет #{ticket_id}",
            description=f"{interaction.user.mention}, опиши проблему. Staff скоро ответит.",
            color=discord.Color.red(),
        )
        await channel.send(content=interaction.user.mention, embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"Тикет создан: {channel.mention}", ephemeral=True)


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel is None:
            return
        close_ticket(interaction.channel.id)
        await interaction.response.send_message("Тикет закрывается.", ephemeral=True)

        log_channel = interaction.guild.get_channel(ticket_log_channel_id()) if interaction.guild else None
        if log_channel:
            await log_channel.send(f"Тикет {interaction.channel.mention} закрыт пользователем {interaction.user.mention}.")

        try:
            await interaction.channel.edit(name=f"closed-{interaction.channel.name}"[:100])
            await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await interaction.channel.set_permissions(interaction.user, view_channel=False)
        except discord.HTTPException:
            pass

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary, custom_id="ticket_claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"Тикет взял в работу {interaction.user.mention}.")
