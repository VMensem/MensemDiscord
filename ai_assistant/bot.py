from __future__ import annotations

import logging
import time

import discord
from discord import app_commands
from discord.ext import commands

from .client import AIClient
from .providers import AIProviderError


EMBED_COLOR = discord.Color.red()
_client: AIClient | None = None


def build_embed(title: str, description: str, *, color: discord.Color = EMBED_COLOR) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color)


def build_error_embed(title: str, description: str) -> discord.Embed:
    return build_embed(title, description, color=discord.Color.red())


def build_response_embed(
    response_text: str,
    provider: str,
    model: str,
    latency_ms: int,
    tokens: tuple[int | None, int | None, int | None],
) -> discord.Embed:
    prompt_tokens, completion_tokens, total_tokens = tokens
    embed = build_embed("AI-ответ", response_text[:4000])
    embed.add_field(name="Провайдер", value=provider, inline=True)
    embed.add_field(name="Модель", value=model, inline=True)
    embed.add_field(name="Время", value=f"{latency_ms} мс", inline=True)
    if any(value is not None for value in tokens):
        usage = []
        if prompt_tokens is not None:
            usage.append(f"prompt: {prompt_tokens}")
        if completion_tokens is not None:
            usage.append(f"completion: {completion_tokens}")
        if total_tokens is not None:
            usage.append(f"total: {total_tokens}")
        embed.add_field(name="Токены", value=" | ".join(usage), inline=False)
    return embed


async def send_error(interaction: discord.Interaction, title: str, description: str) -> None:
    embed = build_error_embed(title, description)
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    global _client
    _client = AIClient()

    @bot.tree.command(name="ai", description="Задать вопрос AI-ассистенту")
    @app_commands.describe(prompt="Что нужно спросить у AI")
    async def ai(interaction: discord.Interaction, prompt: str) -> None:
        assert _client is not None

        if interaction.guild is None:
            return await send_error(interaction, "AI", "Команда доступна только на сервере.")
        if not await _client.is_enabled(interaction.guild.id):
            return await send_error(interaction, "AI отключён", "AI-ассистент сейчас выключен в конфигурации.")
        if not _client.is_ready:
            error = _client.startup_error or AIProviderError("AI недоступен.", code="disabled")
            return await send_error(interaction, "AI недоступен", error.message)
        if not await _client.rate_limit_ok(interaction.user.id, interaction.guild.id):
            return await send_error(interaction, "Лимит", "Слишком много запросов. Попробуй позже.")

        await interaction.response.defer(thinking=True)
        started = time.perf_counter()

        try:
            response = await _client.generate(interaction.user.id, interaction.guild.id, prompt)
        except AIProviderError as exc:
            logging.warning("AI error provider=%s code=%s user_id=%s", _client.provider_name, exc.code, interaction.user.id)
            return await send_error(interaction, "Ошибка AI", exc.message)
        except Exception:
            logging.exception("Unexpected AI failure")
            return await send_error(interaction, "Ошибка AI", "Не удалось получить ответ от AI.")

        total_ms = int((time.perf_counter() - started) * 1000)
        embed = build_response_embed(
            response.text,
            response.provider,
            response.model,
            total_ms,
            (response.prompt_tokens, response.completion_tokens, response.total_tokens),
        )
        embed.set_footer(text=f"Провайдер: {response.provider} | Модель: {response.model}")
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="ai-clear", description="Очистить историю AI")
    async def ai_clear(interaction: discord.Interaction) -> None:
        assert _client is not None
        await _client.clear_history(interaction.user.id)
        await interaction.response.send_message(
            embed=build_embed("AI", "История диалога очищена.", color=discord.Color.green()),
            ephemeral=True,
        )

    print("OK AI module loaded")
