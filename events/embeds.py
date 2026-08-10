import discord

from .config import CONFIG
from .database import count_events


def create_event_embed(title, description, fields=None):
    embed = discord.Embed(title=title, description=description, color=CONFIG["EMBED_COLOR"])
    embed.set_footer(text="Mensem Events System")
    embed.timestamp = discord.utils.utcnow()
    if fields:
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
    return embed


async def create_event_menu_embed(guild: discord.Guild, member: discord.Member) -> discord.Embed:
    total_events, pending_events = await count_events(guild.id)
    embed = discord.Embed(
        title="Управление событиями",
        description="Панель для быстрого создания и контроля событий на сервере.",
        color=CONFIG["EMBED_COLOR"],
    )
    embed.add_field(name="Доступ", value=f"{member.mention} и другие менеджеры событий", inline=False)
    embed.add_field(name="Событий в базе", value=str(total_events), inline=True)
    embed.add_field(name="Ожидают запуска", value=str(pending_events), inline=True)
    embed.add_field(
        name="Что делает меню",
        value=(
            "• создаёт карточку события в текущем канале\n"
            "• пишет запись в базу\n"
            "• ведёт историю действий"
        ),
        inline=False,
    )
    embed.set_footer(text="Mensem Events System")
    embed.timestamp = discord.utils.utcnow()
    return embed
