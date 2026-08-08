from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable

import discord


WINDOW_SECONDS = 600


@dataclass
class LogState:
    message_id: int
    created_at: float
    updated_at: float
    payload: Any


_STATE: dict[tuple[Any, ...], LogState] = {}
_LOCK = asyncio.Lock()


def make_key(*parts: Any) -> tuple[Any, ...]:
    return tuple(parts)


async def clear_stale_states() -> None:
    cutoff = time.time() - WINDOW_SECONDS
    async with _LOCK:
        stale_keys = [key for key, state in _STATE.items() if state.updated_at < cutoff]
        for key in stale_keys:
            _STATE.pop(key, None)


async def upsert_log(
    bot: discord.Client,
    *,
    key: tuple[Any, ...],
    channel_id: int,
    payload: Any,
    build_embed: Callable[[Any, int, float, float], discord.Embed],
    merge_payload: Callable[[Any, Any], Any],
) -> None:
    channel = bot.get_channel(channel_id)
    if channel is None or not hasattr(channel, "send"):
        return

    now = time.time()
    async with _LOCK:
        state = _STATE.get(key)
        can_merge = state is not None and now - state.updated_at <= WINDOW_SECONDS
        if can_merge:
            merged_payload = merge_payload(state.payload, payload)
            created_at = state.created_at
            message_id = state.message_id
        else:
            merged_payload = payload
            created_at = now
            message_id = 0
            state = LogState(message_id=0, created_at=now, updated_at=now, payload=payload)

    count = len(merged_payload.get("entries", [])) if isinstance(merged_payload, dict) and merged_payload.get("entries") is not None else 1
    embed = build_embed(merged_payload, count, created_at, now)

    if can_merge and message_id:
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
            async with _LOCK:
                _STATE[key] = LogState(message_id=message_id, created_at=created_at, updated_at=now, payload=merged_payload)
            return
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            logging.exception("Failed to edit grouped log message")

    message = await channel.send(embed=embed)
    async with _LOCK:
        _STATE[key] = LogState(message_id=message.id, created_at=created_at, updated_at=now, payload=merged_payload)
