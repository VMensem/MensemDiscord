from __future__ import annotations

from datetime import datetime
import logging

import discord

from .batcher import make_key, upsert_log
from .config import LOG_MODERATION_CHANNEL_ID
from .utils import extract_audit_executor


def _build_moderation_embed(payload: dict, count: int, created_at: float, updated_at: float) -> discord.Embed:
    user = payload.get("user")
    executor = payload.get("executor", "Неизвестно")
    executor_id = payload.get("executor_id")
    avatar = payload.get("avatar")
    action = payload.get("action", "action")
    reasons = payload.get("reasons", [])
    server_type = payload.get("server_type", "UNKNOWN")

    title = f"[{server_type}] {'Пользователь заблокирован' if action == 'ban' else 'Пользователь разблокирован'}"
    color = discord.Color.red() if action == "ban" else discord.Color.green()
    embed = discord.Embed(
        title=title,
        description=f"Объединено действий: **{count}**\nОкно: **10 минут**",
        color=color,
    )
    embed.add_field(name="Пользователь", value=f"{user.mention}\n`{user.id}`", inline=False)
    embed.add_field(
        name="Кто сделал",
        value=f"{executor}\n`{executor_id}`" if executor_id else executor,
        inline=False,
    )
    if reasons:
        embed.add_field(name="Причина", value="\n".join(reasons)[:1024], inline=False)
    if avatar:
        embed.set_thumbnail(url=avatar)
    embed.set_footer(text=f"Mensem Logs • {datetime.now().strftime('%d.%m.%Y %H:%M')} • updated")
    return embed


def setup_moderation(bot):
    @bot.listen()
    async def on_member_ban(guild, user):
        if getattr(user, "bot", False):
            return

        executor = "Неизвестно"
        executor_id = None
        reason = "Не указана"
        avatar = None
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
                if getattr(entry.target, "id", None) == user.id:
                    audit = extract_audit_executor(bot, entry)
                    if audit is None:
                        return
                    executor, executor_id, avatar = audit
                    if entry.reason:
                        reason = entry.reason
                    break
        except Exception:
            logging.exception("Failed to inspect ban audit log")

        payload = {
            "user": user,
            "executor": executor,
            "executor_id": executor_id,
            "avatar": avatar,
            "action": "ban",
            "reasons": [reason],
        }

        await upsert_log(
            bot,
            key=make_key("ban", guild.id, user.id, executor_id or executor),
            channel_id=LOG_MODERATION_CHANNEL_ID,
            payload=payload,
            build_embed=_build_moderation_embed,
            merge_payload=lambda old, new: {
                **old,
                "reasons": [*old.get("reasons", []), *new.get("reasons", [])],
                "executor": new.get("executor", old.get("executor")),
                "executor_id": new.get("executor_id", old.get("executor_id")),
                "avatar": new.get("avatar", old.get("avatar")),
            },
        )

    @bot.listen()
    async def on_member_unban(guild, user):
        if getattr(user, "bot", False):
            return

        executor = "Неизвестно"
        executor_id = None
        reason = "Не указана"
        avatar = None
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.unban):
                if getattr(entry.target, "id", None) == user.id:
                    audit = extract_audit_executor(bot, entry)
                    if audit is None:
                        return
                    executor, executor_id, avatar = audit
                    if entry.reason:
                        reason = entry.reason
                    break
        except Exception:
            logging.exception("Failed to inspect unban audit log")

        payload = {
            "user": user,
            "executor": executor,
            "executor_id": executor_id,
            "avatar": avatar,
            "action": "unban",
            "reasons": [reason],
        }

        await upsert_log(
            bot,
            key=make_key("unban", guild.id, user.id, executor_id or executor),
            channel_id=LOG_MODERATION_CHANNEL_ID,
            payload=payload,
            build_embed=_build_moderation_embed,
            merge_payload=lambda old, new: {
                **old,
                "reasons": [*old.get("reasons", []), *new.get("reasons", [])],
                "executor": new.get("executor", old.get("executor")),
                "executor_id": new.get("executor_id", old.get("executor_id")),
                "avatar": new.get("avatar", old.get("avatar")),
            },
        )
