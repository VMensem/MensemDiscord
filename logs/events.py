from __future__ import annotations

from datetime import datetime

import discord

from .batcher import make_key, upsert_log
from .config import LOG_MEMBERS_CHANNEL_ID
from .utils import is_bot_member


def _build_member_embed(payload: dict, count: int, created_at: float, updated_at: float) -> discord.Embed:
    member = payload.get("member")
    kind = payload.get("kind")
    title = "Участник вошёл" if kind == "join" else "Участник вышел"
    color = discord.Color.green() if kind == "join" else discord.Color.red()
    embed = discord.Embed(title=title, color=color)
    embed.add_field(name="Пользователь", value=f"{member.mention}\n`{member.id}`", inline=False)
    if kind == "join":
        embed.add_field(
            name="Аккаунт создан",
            value=f"<t:{int(member.created_at.timestamp())}:F>",
            inline=False,
        )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Mensem Logs • {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    return embed


def setup_events(bot):
    @bot.listen()
    async def on_ready():
        print("OK Logs initialized")

    @bot.listen()
    async def on_member_join(member):
        if is_bot_member(bot, member):
            return

        payload = {"kind": "join", "member": member}
        await upsert_log(
            bot,
            key=make_key("member_join", member.guild.id, member.id),
            channel_id=LOG_MEMBERS_CHANNEL_ID,
            payload=payload,
            build_embed=_build_member_embed,
            merge_payload=lambda old, new: new,
        )

    @bot.listen()
    async def on_member_remove(member):
        if is_bot_member(bot, member):
            return

        payload = {"kind": "leave", "member": member}
        await upsert_log(
            bot,
            key=make_key("member_leave", member.guild.id, member.id),
            channel_id=LOG_MEMBERS_CHANNEL_ID,
            payload=payload,
            build_embed=_build_member_embed,
            merge_payload=lambda old, new: new,
        )
