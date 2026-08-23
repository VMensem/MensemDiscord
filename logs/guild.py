from __future__ import annotations

from datetime import datetime
import logging

import discord

from .batcher import make_key, upsert_log
from .config import LOG_MISC_CHANNEL_ID
from .utils import extract_audit_executor


def _build_guild_embed(payload: dict, count: int, created_at: float, updated_at: float) -> discord.Embed:
    executor = payload.get("executor", "Неизвестно")
    executor_id = payload.get("executor_id")
    avatar = payload.get("avatar")
    changes = payload.get("changes", [])
    server_type = payload.get("server_type", "UNKNOWN")
    embed = discord.Embed(
        title=f"[{server_type}] Сервер изменён",
        description=f"Объединено действий: **{count}**\nОкно: **10 минут**",
        color=discord.Color.orange(),
    )
    if changes:
        embed.add_field(name="Изменения", value="\n\n".join(changes)[:1024], inline=False)
    embed.add_field(
        name="Кто изменил",
        value=f"{executor}\n`{executor_id}`" if executor_id else executor,
        inline=False,
    )
    if avatar:
        embed.set_thumbnail(url=avatar)
    embed.set_footer(text=f"Mensem Logs • {datetime.now().strftime('%d.%m.%Y %H:%M')} • updated")
    return embed


def setup_guild(bot):
    @bot.listen()
    async def on_guild_update(before, after):
        executor = "Неизвестно"
        executor_id = None
        avatar = None
        try:
            async for entry in after.audit_logs(limit=5, action=discord.AuditLogAction.guild_update):
                audit = extract_audit_executor(bot, entry)
                if audit is None:
                    return
                executor, executor_id, avatar = audit
                break
        except Exception:
            logging.exception("Failed to inspect guild update audit log")

        changes = []
        if before.name != after.name:
            changes.append(f"🌍 Название\n`{before.name}`\n⬇️\n`{after.name}`")
        if before.description != after.description:
            changes.append(f"📝 Описание\n`{before.description or 'Нет'}`\n⬇️\n`{after.description or 'Нет'}`")
        if before.system_channel != after.system_channel:
            old = before.system_channel.mention if before.system_channel else "Нет"
            new = after.system_channel.mention if after.system_channel else "Нет"
            changes.append(f"📢 Системный канал\n{old}\n⬇️\n{new}")
        if before.rules_channel != after.rules_channel:
            old = before.rules_channel.mention if before.rules_channel else "Нет"
            new = after.rules_channel.mention if after.rules_channel else "Нет"
            changes.append(f"📚 Канал правил\n{old}\n⬇️\n{new}")
        if before.afk_channel != after.afk_channel:
            old = before.afk_channel.mention if before.afk_channel else "Нет"
            new = after.afk_channel.mention if after.afk_channel else "Нет"
            changes.append(f"💤 AFK канал\n{old}\n⬇️\n{new}")
        if before.afk_timeout != after.afk_timeout:
            changes.append(f"⏳ AFK Timeout\n`{before.afk_timeout}` → `{after.afk_timeout}`")
        if before.verification_level != after.verification_level:
            changes.append(f"🛡️ Проверка\n`{before.verification_level}` → `{after.verification_level}`")
        if before.default_notifications != after.default_notifications:
            changes.append(f"🔔 Уведомления\n`{before.default_notifications}` → `{after.default_notifications}`")
        if before.explicit_content_filter != after.explicit_content_filter:
            changes.append(f"🚫 Контент-фильтр\n`{before.explicit_content_filter}` → `{after.explicit_content_filter}`")
        if before.icon != after.icon:
            changes.append("🖼️ Иконка сервера изменена")
        if before.banner != after.banner:
            changes.append("🎨 Баннер сервера изменён")

        if not changes:
            return

        payload = {
            "executor": executor,
            "executor_id": executor_id,
            "avatar": avatar,
            "changes": changes,
        }

        await upsert_log(
            bot,
            key=make_key("guild", after.id, executor_id or executor),
            channel_id=LOG_MISC_CHANNEL_ID,
            payload=payload,
            build_embed=_build_guild_embed,
            merge_payload=lambda old, new: {
                **old,
                "changes": [*old.get("changes", []), *new.get("changes", [])],
                "executor": new.get("executor", old.get("executor")),
                "executor_id": new.get("executor_id", old.get("executor_id")),
                "avatar": new.get("avatar", old.get("avatar")),
            },
        )
