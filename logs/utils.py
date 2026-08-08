from __future__ import annotations

from typing import Any

import discord


def is_bot_user(user: Any) -> bool:
    return bool(getattr(user, "bot", False))


def is_bot_member(bot: discord.Client, member: Any) -> bool:
    member_id = getattr(member, "id", None)
    return is_bot_user(member) or (
        bot.user is not None and member_id is not None and member_id == bot.user.id
    )


def extract_audit_executor(bot: discord.Client, entry: Any):
    user = getattr(entry, "user", None)
    if user is None or is_bot_user(user) or is_bot_member(bot, user):
        return None

    return user.mention, user.id, user.display_avatar.url
