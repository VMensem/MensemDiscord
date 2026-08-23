import discord
from core.database import db_manager

from .database import close_ticket, create_ticket, check_ticket_exists


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
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
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        category = select.values[0]
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("Тикеты доступны только на сервере.", ephemeral=True)

        if await check_ticket_exists(guild.id, interaction.user.id):
            return await interaction.response.send_message("У вас уже есть открытый тикет.", ephemeral=True)

        settings = await db_manager.get_guild_settings(guild.id)
        target_category_id = settings.get("ticket_category_id") if settings else None
        
        target_category = guild.get_channel(target_category_id) if target_category_id else None
        if target_category_id and not target_category:
            return await interaction.response.send_message("Ошибка конфигурации: Указанная категория тикетов не найдена.", ephemeral=True)
            
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
        except discord.HTTPException:
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

        settings = await db_manager.get_guild_settings(interaction.guild.id) if interaction.guild else None
        log_channel_id = settings.get("ticket_log_channel_id") if settings else None
        
        log_channel = interaction.guild.get_channel(log_channel_id) if interaction.guild and log_channel_id else None
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

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, custom_id="ticket_delete")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel is None:
            return
        
        await interaction.response.send_message("Тикет удаляется.", ephemeral=True)

        settings = await db_manager.get_guild_settings(interaction.guild.id) if interaction.guild else None
        log_channel_id = settings.get("ticket_log_channel_id") if settings else None
        
        log_channel = interaction.guild.get_channel(log_channel_id) if interaction.guild and log_channel_id else None
        if log_channel:
            await log_channel.send(f"Тикет {interaction.channel.name} был удалён.")

        await db_manager.execute("DELETE FROM tickets WHERE channel_id = $1", interaction.channel.id)
        
        try:
            await interaction.channel.delete()
        except discord.HTTPException:
            pass
