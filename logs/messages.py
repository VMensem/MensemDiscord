from __future__ import annotations

from datetime import datetime

import discord

from .batcher import make_key, upsert_log
from .config import LOG_MESSAGES_CHANNEL_ID


def _build_message_embed(payload: dict, count: int, created_at: float, updated_at: float) -> discord.Embed:
    author = payload.get("author")
    channel = payload.get("channel")
    kind = payload.get("kind")
    entries = payload.get("entries", [])

    if kind == "edit":
        title = "Сообщение изменено"
        color = discord.Color.yellow()
    else:
        title = "Сообщение удалено"
        color = discord.Color.red()

    embed = discord.Embed(
        title=title,
        description=f"Объединено событий: **{count}**\nОкно: **10 минут**",
        color=color,
    )
    embed.add_field(name="Автор", value=f"{author.mention}\n`{author.id}`", inline=False)
    embed.add_field(name="Канал", value=channel.mention if channel else "Неизвестно", inline=False)

    lines = []
    for entry in entries:
        if kind == "edit":
            lines.append(f"**Было:** {entry['before']}\n**Стало:** {entry['after']}")
        else:
            lines.append(entry["content"])

    field_name = "Изменения" if kind == "edit" else "Удалённый текст"
    embed.add_field(name=field_name, value="\n\n".join(lines)[:1024] or "Нет текста", inline=False)
    embed.set_thumbnail(url=author.display_avatar.url)
    embed.set_footer(text=f"Mensem Logs • {datetime.now().strftime('%d.%m.%Y %H:%M')} • updated")
    return embed


def setup_messages(bot):
    @bot.listen()
    async def on_message_delete(message):
        if message.guild is None or getattr(message.author, "bot", False):
            return

        payload = {
            "kind": "delete",
            "author": message.author,
            "channel": message.channel,
            "entries": [{"content": message.content[:1024] or "Нет текста"}],
        }

        await upsert_log(
            bot,
            key=make_key("message_delete", message.guild.id, message.channel.id, message.author.id),
            channel_id=LOG_MESSAGES_CHANNEL_ID,
            payload=payload,
            build_embed=_build_message_embed,
            merge_payload=lambda old, new: {
                **old,
                "entries": [*old.get("entries", []), *new.get("entries", [])],
            },
        )

    @bot.listen()
    async def on_message_edit(before, after):
        if before.guild is None or getattr(before.author, "bot", False) or before.content == after.content:
            return

        payload = {
            "kind": "edit",
            "author": before.author,
            "channel": before.channel,
            "entries": [{"before": before.content[:1024] or "Нет текста", "after": after.content[:1024] or "Нет текста"}],
        }

        await upsert_log(
            bot,
            key=make_key("message_edit", before.guild.id, before.channel.id, before.author.id),
            channel_id=LOG_MESSAGES_CHANNEL_ID,
            payload=payload,
            build_embed=_build_message_embed,
            merge_payload=lambda old, new: {
                **old,
                "entries": [*old.get("entries", []), *new.get("entries", [])],
            },
        )
