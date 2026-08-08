from __future__ import annotations

from datetime import datetime
import logging

import discord

from .batcher import make_key, upsert_log
from .config import LOG_CHANNELS_CHANNEL_ID
from .utils import extract_audit_executor, is_bot_member


def _build_channel_embed(payload: dict, count: int, created_at: float, updated_at: float) -> discord.Embed:
    kind = payload.get("kind")
    channel = payload.get("channel")
    executor = payload.get("executor", "Неизвестно")
    executor_id = payload.get("executor_id")
    avatar = payload.get("avatar")
    changes = payload.get("changes", [])

    title_map = {
        "create": "Канал создан",
        "delete": "Канал удалён",
        "update": "Канал изменён",
    }
    color_map = {
        "create": discord.Color.green(),
        "delete": discord.Color.red(),
        "update": discord.Color.orange(),
    }

    embed = discord.Embed(
        title=title_map.get(kind, "Канал"),
        description=f"Объединено действий: **{count}**\nОкно: **10 минут**",
        color=color_map.get(kind, discord.Color.orange()),
    )
    embed.add_field(name="Канал", value=f"{channel.mention}\n`{channel.id}`", inline=False)
    embed.add_field(
        name="Кто сделал",
        value=f"{executor}\n`{executor_id}`" if executor_id else executor,
        inline=False,
    )
    if changes:
        embed.add_field(name="Изменения", value="\n\n".join(changes)[:1024], inline=False)
    if avatar:
        embed.set_thumbnail(url=avatar)
    embed.set_footer(text=f"Mensem Logs • {datetime.now().strftime('%d.%m.%Y %H:%M')} • updated")
    return embed


def _merge(old: dict, new: dict) -> dict:
    return {
        **old,
        "changes": [*old.get("changes", []), *new.get("changes", [])],
        "executor": new.get("executor", old.get("executor")),
        "executor_id": new.get("executor_id", old.get("executor_id")),
        "avatar": new.get("avatar", old.get("avatar")),
    }


def setup_channels(bot):
    @bot.listen()
    async def on_guild_channel_create(channel):
        if channel.guild is None:
            return

        try:
            async for entry in channel.guild.audit_logs(limit=10, action=discord.AuditLogAction.channel_create):
                if getattr(entry.target, "id", None) == channel.id:
                    audit = extract_audit_executor(bot, entry)
                    if audit is None:
                        return
                    executor, executor_id, avatar = audit
                    break
            else:
                executor, executor_id, avatar = "Неизвестно", None, None
        except Exception:
            logging.exception("Failed to inspect channel create audit log")
            executor, executor_id, avatar = "Неизвестно", None, None

        payload = {
            "kind": "create",
            "channel": channel,
            "executor": executor,
            "executor_id": executor_id,
            "avatar": avatar,
            "changes": [f"📁 Категория: {channel.category.mention if channel.category else 'Нет'}"],
        }
        await upsert_log(
            bot,
            key=make_key("channel_create", channel.guild.id, channel.id, executor_id or executor),
            channel_id=LOG_CHANNELS_CHANNEL_ID,
            payload=payload,
            build_embed=_build_channel_embed,
            merge_payload=_merge,
        )

    @bot.listen()
    async def on_guild_channel_delete(channel):
        if channel.guild is None:
            return

        try:
            async for entry in channel.guild.audit_logs(limit=10, action=discord.AuditLogAction.channel_delete):
                if getattr(entry.target, "id", None) == channel.id:
                    audit = extract_audit_executor(bot, entry)
                    if audit is None:
                        return
                    executor, executor_id, avatar = audit
                    break
            else:
                executor, executor_id, avatar = "Неизвестно", None, None
        except Exception:
            logging.exception("Failed to inspect channel delete audit log")
            executor, executor_id, avatar = "Неизвестно", None, None

        payload = {
            "kind": "delete",
            "channel": channel,
            "executor": executor,
            "executor_id": executor_id,
            "avatar": avatar,
            "changes": [f"`{channel.name}`"],
        }
        await upsert_log(
            bot,
            key=make_key("channel_delete", channel.guild.id, channel.id, executor_id or executor),
            channel_id=LOG_CHANNELS_CHANNEL_ID,
            payload=payload,
            build_embed=_build_channel_embed,
            merge_payload=_merge,
        )

    @bot.listen()
    async def on_guild_channel_update(before, after):
        if before.guild is None or is_bot_member(bot, after):
            return

        changes = []
        if before.name != after.name:
            changes.append(f"📝 Название: `{before.name}` → `{after.name}`")
        if before.category != after.category:
            old = before.category.name if before.category else "Нет"
            new = after.category.name if after.category else "Нет"
            changes.append(f"📁 Категория: `{old}` → `{new}`")
        if before.overwrites != after.overwrites:
            changes.append("⚙️ Изменены права доступа")

        if not changes:
            return

        try:
            async for entry in after.guild.audit_logs(limit=10, action=discord.AuditLogAction.channel_update):
                if getattr(entry.target, "id", None) == after.id:
                    audit = extract_audit_executor(bot, entry)
                    if audit is None:
                        return
                    executor, executor_id, avatar = audit
                    break
            else:
                executor, executor_id, avatar = "Неизвестно", None, None
        except Exception:
            logging.exception("Failed to inspect channel update audit log")
            executor, executor_id, avatar = "Неизвестно", None, None

        payload = {
            "kind": "update",
            "channel": after,
            "executor": executor,
            "executor_id": executor_id,
            "avatar": avatar,
            "changes": changes,
        }
        await upsert_log(
            bot,
            key=make_key("channel_update", after.guild.id, after.id, executor_id or executor),
            channel_id=LOG_CHANNELS_CHANNEL_ID,
            payload=payload,
            build_embed=_build_channel_embed,
            merge_payload=_merge,
        )
