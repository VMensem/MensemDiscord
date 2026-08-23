from __future__ import annotations

import logging
import time
import re

import discord
from discord import app_commands
from discord.ext import commands

from .client import AIClient
from .providers import AIProviderError
from .knowledge_base import upsert_knowledge


EMBED_COLOR = discord.Color.red()
_client: AIClient | None = None


def build_embed(title: str, description: str, *, color: discord.Color = EMBED_COLOR) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color)


def build_error_embed(title: str, description: str) -> discord.Embed:
    return build_embed(title, description, color=discord.Color.red())


def build_response_embed(
    response_text: str,
) -> discord.Embed:
    # Make text bold for better readability
    description = f"**{response_text}**"
    embed = build_embed("", description[:4000])
    
    # Add footer in the format: Mensem • AI Assistant • HH:MM
    from datetime import datetime
    now = datetime.now().strftime("%H:%M")
    embed.set_footer(text=f"Mensem • AI Assistant • {now}")
    
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
        
        await interaction.response.defer(thinking=True)
        logging.info("[AI] Interaction deferred")

        if not await _client.rate_limit_ok(interaction.user.id, interaction.guild.id):
            return await send_error(interaction, "Лимит", "Слишком много запросов. Попробуй позже.")

        # Fact saving logic
        trigger_pattern = r'^(запомни[:\s]+что|запомни:|сохрани[:\s]+информацию:|сохрани:|факт:|запиши:)\s*(.*)'
        match = re.match(trigger_pattern, prompt, re.IGNORECASE)
        if match:
            content = match.group(2).strip()
            if not content:
                return await interaction.followup.send(embed=build_embed("Ошибка", "Нечего запоминать."), ephemeral=True)
            
            success = await upsert_knowledge(interaction.guild.id, content)
            if success:
                return await interaction.followup.send(embed=build_embed("AI", "Запомнил! 🧠", color=discord.Color.green()))
            else:
                return await interaction.followup.send(embed=build_embed("AI", "Эта информация уже сохранена.", color=discord.Color.yellow()))

        started = time.perf_counter()
        logging.info("[AI] /ai interaction received: %s", prompt)

        try:
            response = await _client.generate(interaction.user.id, interaction.guild.id, prompt)
        except AIProviderError as exc:
            logging.warning("AI error provider=%s code=%s user_id=%s", _client.provider_name, exc.code, interaction.user.id)
            return await send_error(interaction, "Ошибка AI", exc.message)
        except Exception:
            logging.exception("Unexpected AI failure")
            return await send_error(interaction, "Ошибка AI", "Не удалось получить ответ от AI.")

        total_ms = int((time.perf_counter() - started) * 1000)
        logging.info("[AI] Response received, sending Discord response")
        embed = build_response_embed(response.text)
        await interaction.followup.send(embed=embed)
        logging.info("[AI] Response sent successfully")

    @bot.tree.command(name="ai-clear", description="Очистить историю AI")
    async def ai_clear(interaction: discord.Interaction) -> None:
        assert _client is not None
        await _client.clear_history(interaction.user.id)
        await interaction.response.send_message(
            embed=build_embed("AI", "История диалога очищена.", color=discord.Color.green()),
            ephemeral=True,
        )

    print("OK AI module loaded")
