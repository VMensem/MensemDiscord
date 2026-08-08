from __future__ import annotations

from datetime import datetime
import logging

import discord

from .batcher import make_key, upsert_log
from .config import LOG_ROLES_CHANNEL_ID
from .utils import extract_audit_executor, is_bot_member


def _entry_name(role: discord.Role) -> str:
    return "@everyone" if role.is_default() else role.mention


def _build_roles_embed(payload: dict, count: int, created_at: float, updated_at: float) -> discord.Embed:
    entries = payload.get("entries", [])
    member_name = payload.get("member_name", "Unknown")
    member_id = payload.get("member_id", 0)
    executor = payload.get("executor", "Неизвестно")
    executor_id = payload.get("executor_id")
    avatar = payload.get("executor_avatar")

    added = []
    removed = []
    for entry in entries:
        line = f"`{entry['role_name']}` (`{entry['role_id']}`)"
        if entry["kind"] == "add":
            added.append(line)
        else:
            removed.append(line)

    color = discord.Color.orange()
    if added and not removed:
        color = discord.Color.green()
    elif removed and not added:
        color = discord.Color.red()

    embed = discord.Embed(
        title="Роли обновлены",
        description=f"Объединено действий: **{count}**\nОкно: **10 минут**",
        color=color,
    )
    embed.add_field(name="Пользователь", value=f"{member_name}\n`{member_id}`", inline=False)
    embed.add_field(
        name="Кто сделал",
        value=f"{executor}\n`{executor_id}`" if executor_id else executor,
        inline=False,
    )

    changes = []
    if added:
        changes.append("➕ Добавлено:\n" + "\n".join(added))
    if removed:
        changes.append("➖ Убрано:\n" + "\n".join(removed))
    embed.add_field(name="Изменения", value="\n\n".join(changes)[:1024] or "Нет изменений", inline=False)

    if avatar:
        embed.set_thumbnail(url=avatar)
    embed.set_footer(text=f"Mensem Logs • {datetime.now().strftime('%d.%m.%Y %H:%M')} • updated")
    return embed


def setup_roles(bot):
    @bot.listen()
    async def on_member_update(before, after):
        if is_bot_member(bot, after) or before.roles == after.roles:
            return

        added_roles = [role for role in after.roles if role not in before.roles and not role.is_default()]
        removed_roles = [role for role in before.roles if role not in after.roles and not role.is_default()]
        if not added_roles and not removed_roles:
            return

        try:
            async for entry in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_role_update):
                if getattr(entry.target, "id", None) == after.id:
                    audit = extract_audit_executor(bot, entry)
                    if audit is None:
                        return
                    executor, executor_id, avatar = audit
                    break
            else:
                executor, executor_id, avatar = "Неизвестно", None, None
        except Exception:
            logging.exception("Failed to inspect role update audit log")
            executor, executor_id, avatar = "Неизвестно", None, None

        payload = {
            "member_id": after.id,
            "member_name": after.display_name,
            "executor": executor,
            "executor_id": executor_id,
            "executor_avatar": avatar,
            "entries": [
                {"kind": "add", "role_name": _entry_name(role), "role_id": role.id}
                for role in added_roles
            ]
            + [
                {"kind": "remove", "role_name": _entry_name(role), "role_id": role.id}
                for role in removed_roles
            ],
        }

        key = make_key("roles", after.guild.id, after.id, executor_id or executor)
        await upsert_log(
            bot,
            key=key,
            channel_id=LOG_ROLES_CHANNEL_ID,
            payload=payload,
            build_embed=_build_roles_embed,
            merge_payload=lambda old, new: {
                **old,
                "entries": [*old.get("entries", []), *new.get("entries", [])],
                "executor": new.get("executor", old.get("executor")),
                "executor_id": new.get("executor_id", old.get("executor_id")),
                "executor_avatar": new.get("executor_avatar", old.get("executor_avatar")),
                "member_name": new.get("member_name", old.get("member_name")),
            },
        )
