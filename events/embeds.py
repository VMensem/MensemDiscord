import discord

from .config import CONFIG
from .api_client import api_client


def create_event_embed(title, description, fields=None):
    embed = discord.Embed(title=title, description=description, color=CONFIG["EMBED_COLOR"])
    embed.set_footer(text="Mensem Events System")
    embed.timestamp = discord.utils.utcnow()
    if fields:
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
    return embed


async def create_event_menu_embed(guild: discord.Guild, member: discord.Member) -> discord.Embed:
    # Заменяем вызов database.py на API
    response = await api_client.get_events(guild_id=guild.id)
    
    total_events = 0
    pending_events = 0
    
    if response and response.get("data"):
        events = response["data"]
        # Фильтруем события по серверу, если нужно (предполагаем, что API возвращает все или отфильтрованные)
        # В текущей реализации API возвращает всё, фильтруем по guild_id
        guild_events = [e for e in events if str(e.get("guild_id")) == str(guild.id)]
        total_events = len(guild_events)
        pending_events = len([e for e in guild_events if e.get("state") == "draft"])
    
    embed = discord.Embed(
        title="Управление событиями",
        description="Панель для быстрого создания и контроля событий на сервере.",
        color=CONFIG["EMBED_COLOR"],
    )
    embed.add_field(name="Доступ", value=f"{member.mention} и другие менеджеры событий", inline=False)
    embed.add_field(name="Событий в Mensem Events", value=str(total_events), inline=True)
    embed.add_field(name="Ожидают запуска", value=str(pending_events), inline=True)
    embed.add_field(
        name="Что делает меню",
        value=(
            "• создаёт карточку события в Discord\n"
            "• управляет событиями через Mensem Events API\n"
            "• отображает актуальную статистику"
        ),
        inline=False,
    )
    embed.set_footer(text="Mensem Events System")
    embed.timestamp = discord.utils.utcnow()
    return embed
