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
        self.add_item(self.category_select())

    def category_select(self):
        select = discord.ui.Select(
            placeholder="Выберите категорию тикета",
            custom_id="ticket_category_select",
            options=[
                discord.SelectOption(label="Support", description="Помощь по серверу", value="Support", emoji="🛠️"),
                discord.SelectOption(label="Жалоба", description="Подать жалобу", value="Report", emoji="📋"),
                discord.SelectOption(label="Репорт", description="Репорт игрока", value="Complaint", emoji="⚠️"),
                discord.SelectOption(label="Донат", description="Вопросы по донату", value="Donation", emoji="💰"),
                discord.SelectOption(label="Другое", description="Другие вопросы", value="Other", emoji="❓"),
            ],
        )
        select.callback = self.select_callback
        return select

    async def select_callback(self, interaction: discord.Interaction):
        category = interaction.data["values"][0]
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("Тикеты доступны только на сервере.", ephemeral=True)

        target_category = guild.get_channel(ticket_category_id()) if ticket_category_id() else None
        if target_category and not isinstance(target_category, discord.CategoryChannel):
            return await interaction.response.send_message("Ошибка конфигурации: Указанная категория тикетов не является категорией Discord.", ephemeral=True)
            
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        
        name = f"ticket-{category.lower()}-{interaction.user.name}".lower().replace(" ", "-")[:90]
        try:
            channel = await guild.create_text_channel(name=name, category=target_category, overwrites=overwrites)
        except discord.Forbidden:
            return await interaction.response.send_message("У бота нет прав на создание тикетов.", ephemeral=True)
        except discord.HTTPException as e:
            if e.code == 50024:
                return await interaction.response.send_message("Ошибка: Указанная категория тикетов не является категорией Discord.", ephemeral=True)
            return await interaction.response.send_message("Не удалось создать канал тикета.", ephemeral=True)

        ticket_id = await create_ticket(guild.id, interaction.user.id, channel.id, category_id=category)
        embed = discord.Embed(
            title=f"Тикет #{ticket_id} | {category}",
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
        await close_ticket(interaction.channel.id)
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
