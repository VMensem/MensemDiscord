from __future__ import annotations

import logging
from datetime import datetime

import discord
from discord.ui import Modal, TextInput, View

from .database import get_owner, update_room_owner


def _bot_member(guild: discord.Guild) -> discord.Member | None:
    return guild.me


def _guild_text_channel(guild: discord.Guild) -> discord.abc.Messageable | None:
    bot_member = _bot_member(guild)
    if bot_member is None:
        return None

    if guild.system_channel and guild.system_channel.permissions_for(bot_member).send_messages:
        return guild.system_channel

    for channel in guild.text_channels:
        if channel.permissions_for(bot_member).send_messages:
            return channel

    return None


def _voice_channel(interaction: discord.Interaction) -> discord.VoiceChannel | None:
    member = interaction.user if isinstance(interaction.user, discord.Member) else None
    if member is None or member.voice is None or member.voice.channel is None:
        return None
    channel = member.voice.channel
    return channel if isinstance(channel, discord.VoiceChannel) else None


async def _can_manage(interaction: discord.Interaction, channel: discord.VoiceChannel) -> bool:
    member = interaction.user if isinstance(interaction.user, discord.Member) else None
    if member is None:
        return False
    if member.guild_permissions.administrator:
        return True
    owner_id = await get_owner(channel.id)
    return owner_id == member.id


async def _require_channel(interaction: discord.Interaction) -> discord.VoiceChannel | None:
    channel = _voice_channel(interaction)
    if channel is None:
        await interaction.response.send_message("Сначала зайди в голосовой канал.", ephemeral=True)
        return None
    return channel


class VoicePanel(View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        channel = _voice_channel(interaction)
        if channel is None:
            await interaction.response.send_message("Сначала зайди в голосовой канал.", ephemeral=True)
            return False

        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None:
            await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)
            return False

        owner_id = await get_owner(channel.id)
        if owner_id is None:
            owner_id = self.owner_id

        if member.id == owner_id or member.guild_permissions.administrator:
            return True

        await interaction.response.send_message("Только владелец комнаты может использовать панель.", ephemeral=True)
        return False

    @discord.ui.button(emoji="✏️", label="Название", style=discord.ButtonStyle.blurple)
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RenameModal())

    @discord.ui.button(emoji="👥", label="Лимит", style=discord.ButtonStyle.blurple)
    async def limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LimitModal())

    @discord.ui.button(emoji="🗝️", label="Передать", style=discord.ButtonStyle.secondary)
    async def transfer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TransferModal())

    @discord.ui.button(emoji="🔒", label="Закрыть", style=discord.ButtonStyle.danger)
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await _require_channel(interaction)
        if channel is None:
            return

        if not await _can_manage(interaction, channel):
            return await interaction.response.send_message("Эта панель доступна только владельцу комнаты.", ephemeral=True)

        overwrite = channel.overwrites_for(channel.guild.default_role)
        overwrite.connect = False
        await channel.set_permissions(channel.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("Комната закрыта.", ephemeral=True)

    @discord.ui.button(emoji="🔓", label="Открыть", style=discord.ButtonStyle.success)
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await _require_channel(interaction)
        if channel is None:
            return

        if not await _can_manage(interaction, channel):
            return await interaction.response.send_message("Эта панель доступна только владельцу комнаты.", ephemeral=True)

        overwrite = channel.overwrites_for(channel.guild.default_role)
        overwrite.connect = None
        await channel.set_permissions(channel.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("Комната открыта.", ephemeral=True)

    @discord.ui.button(emoji="🙈", label="Скрыть", style=discord.ButtonStyle.secondary)
    async def hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await _require_channel(interaction)
        if channel is None:
            return

        if not await _can_manage(interaction, channel):
            return await interaction.response.send_message("Эта панель доступна только владельцу комнаты.", ephemeral=True)

        overwrite = channel.overwrites_for(channel.guild.default_role)
        overwrite.view_channel = False
        await channel.set_permissions(channel.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("Комната скрыта.", ephemeral=True)

    @discord.ui.button(emoji="👁️", label="Показать", style=discord.ButtonStyle.success)
    async def show(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await _require_channel(interaction)
        if channel is None:
            return

        if not await _can_manage(interaction, channel):
            return await interaction.response.send_message("Эта панель доступна только владельцу комнаты.", ephemeral=True)

        overwrite = channel.overwrites_for(channel.guild.default_role)
        overwrite.view_channel = None
        await channel.set_permissions(channel.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("Комната снова видима.", ephemeral=True)

    @discord.ui.button(emoji="🗑️", label="Удалить", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await _require_channel(interaction)
        if channel is None:
            return

        if not await _can_manage(interaction, channel):
            return await interaction.response.send_message("Эта панель доступна только владельцу комнаты.", ephemeral=True)

        await interaction.response.send_message("Комната удаляется...", ephemeral=True)
        try:
            await channel.delete()
        except Exception:
            logging.exception("Failed to delete voice channel from panel")


class RenameModal(Modal):
    def __init__(self):
        super().__init__(title="Изменить название")
        self.name_input = TextInput(label="Новое название", max_length=100)
        self.add_item(self.name_input)

    async def on_submit(self, interaction: discord.Interaction):
        channel = await _require_channel(interaction)
        if channel is None:
            return

        if not await _can_manage(interaction, channel):
            return await interaction.response.send_message("Эта панель доступна только владельцу комнаты.", ephemeral=True)

        new_name = self.name_input.value.strip()
        if not new_name:
            return await interaction.response.send_message("Название не может быть пустым.", ephemeral=True)

        await channel.edit(name=new_name)
        await interaction.response.send_message("Название изменено.", ephemeral=True)


class LimitModal(Modal):
    def __init__(self):
        super().__init__(title="Изменить лимит")
        self.limit_input = TextInput(label="Лимит (0-99)")
        self.add_item(self.limit_input)

    async def on_submit(self, interaction: discord.Interaction):
        channel = await _require_channel(interaction)
        if channel is None:
            return

        if not await _can_manage(interaction, channel):
            return await interaction.response.send_message("Эта панель доступна только владельцу комнаты.", ephemeral=True)

        try:
            limit = int(self.limit_input.value)
        except ValueError:
            return await interaction.response.send_message("Лимит должен быть числом.", ephemeral=True)

        if limit < 0 or limit > 99:
            return await interaction.response.send_message("Лимит должен быть от 0 до 99.", ephemeral=True)

        await channel.edit(user_limit=limit)
        await interaction.response.send_message("Лимит изменён.", ephemeral=True)


class TransferModal(Modal):
    def __init__(self):
        super().__init__(title="Передать владельца")
        self.user_input = TextInput(label="ID пользователя")
        self.add_item(self.user_input)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)

        channel = await _require_channel(interaction)
        if channel is None:
            return

        if not await _can_manage(interaction, channel):
            return await interaction.response.send_message("Эта панель доступна только владельцу комнаты.", ephemeral=True)

        try:
            member_id = int(self.user_input.value)
        except ValueError:
            return await interaction.response.send_message("Нужен числовой ID пользователя.", ephemeral=True)

        member = interaction.guild.get_member(member_id)
        if member is None:
            try:
                member = await interaction.guild.fetch_member(member_id)
            except discord.NotFound:
                return await interaction.response.send_message("Пользователь не найден.", ephemeral=True)
            except discord.HTTPException:
                return await interaction.response.send_message("Не удалось загрузить пользователя.", ephemeral=True)

        if member.bot:
            return await interaction.response.send_message("Нельзя передать комнату боту.", ephemeral=True)

        current_owner_id = await get_owner(channel.id)
        if current_owner_id == member.id:
            return await interaction.response.send_message("Этот пользователь уже является владельцем.", ephemeral=True)

        old_owner = interaction.guild.get_member(current_owner_id) if current_owner_id else None
        if old_owner is not None:
            try:
                await channel.set_permissions(old_owner, overwrite=None)
            except discord.HTTPException:
                logging.exception("Failed to clear old owner permissions")

        await channel.set_permissions(
            member,
            manage_channels=True,
            move_members=True,
            mute_members=True,
            deafen_members=True,
            connect=True,
        )
        await update_room_owner(channel.id, member.id)
        await interaction.response.send_message(f"Владелец передан {member.mention}", ephemeral=True)


async def send_panel(channel, owner):
    guild = channel.guild
    target_channel = _guild_text_channel(guild)
    if target_channel is None:
        logging.warning("No text channel found for voice panel in guild %s", guild.id)
        return False

    embed = discord.Embed(
        title="Управление комнатой",
        description="Управляйте своей временной голосовой комнатой.",
        color=discord.Color.red(),
    )
    embed.add_field(name="Владелец", value=owner.mention, inline=True)
    embed.add_field(name="Название", value=channel.name, inline=True)
    embed.add_field(name="Лимит", value=channel.user_limit or "∞", inline=True)
    embed.set_thumbnail(url=owner.display_avatar.url)
    embed.set_footer(text=f"Mensem Voice • {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    await target_channel.send(embed=embed, view=VoicePanel(owner.id))
    return True
