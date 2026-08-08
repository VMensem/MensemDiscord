from __future__ import annotations

from datetime import datetime

import discord

from .batcher import make_key, upsert_log
from .config import LOG_VOICE_CHANNEL_ID
from .utils import is_bot_member


def _build_voice_embed(payload: dict, count: int, created_at: float, updated_at: float) -> discord.Embed:
    kind = payload.get("kind")
    member = payload.get("member")
    entries = payload.get("entries", [])

    if kind == "join":
        title = "Подключение к голосовому каналу"
        color = discord.Color.green()
    elif kind == "leave":
        title = "Выход из голосового канала"
        color = discord.Color.red()
    else:
        title = "Переход между голосовыми каналами"
        color = discord.Color.orange()

    embed = discord.Embed(
        title=title,
        description=f"Объединено событий: **{count}**\nОкно: **10 минут**",
        color=color,
    )
    embed.add_field(name="Пользователь", value=f"{member.mention}\n`{member.id}`", inline=False)

    lines = []
    for entry in entries:
        if kind == "join":
            lines.append(f"Присоединился: {entry['after']}")
        elif kind == "leave":
            lines.append(f"Покинул: {entry['before']}")
        else:
            lines.append(f"{entry['before']} → {entry['after']}")

    embed.add_field(name="Каналы", value="\n".join(lines)[:1024] or "Нет изменений", inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Mensem Logs • {datetime.now().strftime('%d.%m.%Y %H:%M')} • updated")
    return embed


def setup_voice(bot):
    @bot.listen()
    async def on_voice_state_update(member, before, after):
        if is_bot_member(bot, member):
            return

        if before.channel is None and after.channel is not None:
            payload = {
                "kind": "join",
                "member": member,
                "entries": [{"after": after.channel.mention}],
            }
            await upsert_log(
                bot,
                key=make_key("voice_join", member.guild.id, member.id, after.channel.id),
                channel_id=LOG_VOICE_CHANNEL_ID,
                payload=payload,
                build_embed=_build_voice_embed,
                merge_payload=lambda old, new: {
                    **old,
                    "entries": [*old.get("entries", []), *new.get("entries", [])],
                },
            )
            return

        if before.channel is not None and after.channel is None:
            payload = {
                "kind": "leave",
                "member": member,
                "entries": [{"before": before.channel.mention}],
            }
            await upsert_log(
                bot,
                key=make_key("voice_leave", member.guild.id, member.id, before.channel.id),
                channel_id=LOG_VOICE_CHANNEL_ID,
                payload=payload,
                build_embed=_build_voice_embed,
                merge_payload=lambda old, new: {
                    **old,
                    "entries": [*old.get("entries", []), *new.get("entries", [])],
                },
            )
            return

        if before.channel is not None and after.channel is not None and before.channel != after.channel:
            payload = {
                "kind": "move",
                "member": member,
                "entries": [{"before": before.channel.mention, "after": after.channel.mention}],
            }
            await upsert_log(
                bot,
                key=make_key("voice_move", member.guild.id, member.id, before.channel.id, after.channel.id),
                channel_id=LOG_VOICE_CHANNEL_ID,
                payload=payload,
                build_embed=_build_voice_embed,
                merge_payload=lambda old, new: {
                    **old,
                    "entries": [*old.get("entries", []), *new.get("entries", [])],
                },
            )
