from __future__ import annotations

import re
import logging
import time
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from .config import config
from .database import init_database, load_stats_db, save_stats_db


MENTION_RE = re.compile(r"^<@!?(\d+)>$")
EMBED_COLOR = discord.Color.red()
MSK_TZ = timezone(timedelta(hours=3), "MSK")

voice_total_seconds: dict[str, int] = {}
support_daily_seconds: dict[str, dict[str, int]] = {}
support_action_stats: dict[str, dict[str, dict]] = {}
voice_joined_at: dict[str, float] = {}
daily_report_sent_dates: set[str] = set()


def today_key() -> str:
    return datetime.now(MSK_TZ).date().isoformat()


def is_verifier(member: discord.Member) -> bool:
    verifier_roles = set(config.VERIFIER_ROLES)
    return any(role.id in verifier_roles for role in member.roles)


def is_passing_channel(channel: discord.abc.GuildChannel | None) -> bool:
    return bool(channel and channel.id in config.PASSING_CHANNELS)


def is_in_passing(member: discord.Member) -> bool:
    return bool(member.voice and member.voice.channel and is_passing_channel(member.voice.channel))


def parse_member_id(value: str) -> int | None:
    value = value.strip()
    mention = MENTION_RE.match(value)
    if mention:
        return int(mention.group(1))
    if value.isdigit():
        return int(value)
    return None


def user_label(user: discord.abc.User) -> str:
    return getattr(user, "display_name", None) or user.name


def review_image_url(user: discord.abc.User) -> str:
    return config.REVIEW_IMAGE or user.display_avatar.url


async def resolve_member(interaction: discord.Interaction, value: str) -> discord.Member | None:
    if interaction.guild is None:
        return None

    member_id = parse_member_id(value)
    if member_id is not None:
        member = interaction.guild.get_member(member_id)
        if member is not None:
            return member
        try:
            return await interaction.guild.fetch_member(member_id)
        except discord.NotFound:
            return None

    lowered = value.lower()
    for member in interaction.guild.members:
        if member.name.lower() == lowered or member.display_name.lower() == lowered:
            return member
    return None


async def get_configured_role(guild: discord.Guild, role_key: str) -> discord.Role | None:
    role_id = config.ROLES.get(role_key, 0)
    if not role_id:
        return None

    role = guild.get_role(role_id)
    if role is not None:
        return role

    try:
        roles = await guild.fetch_roles()
    except discord.HTTPException:
        return None
    return discord.utils.get(roles, id=role_id)


def load_stats() -> None:
    global voice_total_seconds, support_daily_seconds, support_action_stats, voice_joined_at, daily_report_sent_dates
    (
        voice_total_seconds,
        support_daily_seconds,
        support_action_stats,
        voice_joined_at,
        daily_report_sent_dates,
    ) = load_stats_db()


def save_stats() -> None:
    save_stats_db(
        voice_total_seconds,
        support_daily_seconds,
        support_action_stats,
        voice_joined_at,
        daily_report_sent_dates,
    )


def add_voice_seconds(member_id: int, seconds: int) -> None:
    if seconds <= 0:
        return
    key = str(member_id)
    day = today_key()
    voice_total_seconds[key] = voice_total_seconds.get(key, 0) + seconds
    support_daily_seconds.setdefault(day, {})[key] = support_daily_seconds.setdefault(day, {}).get(key, 0) + seconds


def add_action(member_id: int, action: str) -> None:
    day = today_key()
    stats = support_action_stats.setdefault(day, {}).setdefault(
        str(member_id),
        {"verified": 0, "no_access": 0, "reviews": []},
    )
    stats[action] = int(stats.get(action, 0) or 0) + 1


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(max(0, int(seconds)), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}ч {minutes}м"
    if minutes:
        return f"{minutes}м {seconds}с"
    return f"{seconds}с"


def current_week_days() -> list[datetime]:
    today = datetime.now(MSK_TZ).date()
    start = today - timedelta(days=today.weekday())
    return [datetime.combine(start + timedelta(days=offset), datetime.min.time(), tzinfo=MSK_TZ) for offset in range(7)]


def week_day_options() -> list[tuple[str, str]]:
    names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    options = [("week", "За неделю")]
    for day, name in zip(current_week_days(), names, strict=True):
        options.append((day.date().isoformat(), name))
    return options


def period_day_keys(period: str) -> list[str]:
    if period == "week":
        return [day.date().isoformat() for day in current_week_days()]
    return [period]


def period_label(period: str) -> str:
    for value, label in week_day_options():
        if value == period:
            return label
    return "Выбранный день"


def support_seconds_for_day(member: discord.Member, day: str, now_ts: float) -> int:
    seconds = int(support_daily_seconds.get(day, {}).get(str(member.id), 0) or 0)
    if day == today_key() and str(member.id) in voice_joined_at and is_in_passing(member):
        seconds += int(now_ts - voice_joined_at[str(member.id)])
    return seconds


def support_seconds_for_period(member: discord.Member, days: list[str], now_ts: float) -> int:
    return sum(support_seconds_for_day(member, day, now_ts) for day in days)


def support_action_totals(member_id: int, days: list[str]) -> tuple[int, int]:
    verified = 0
    no_access = 0
    member_key = str(member_id)
    for day in days:
        stats = support_action_stats.get(day, {}).get(member_key, {})
        if not isinstance(stats, dict):
            continue
        verified += int(stats.get("verified", 0) or 0)
        no_access += int(stats.get("no_access", 0) or 0)
    return verified, no_access


def support_review_records(member_id: int, days: list[str]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    member_key = str(member_id)
    for day in days:
        stats = support_action_stats.get(day, {}).get(member_key, {})
        if not isinstance(stats, dict):
            continue
        reviews = stats.get("reviews", [])
        if isinstance(reviews, list):
            records.extend(review for review in reviews if isinstance(review, dict))
    records.sort(key=lambda review: str(review.get("timestamp", "")), reverse=True)
    return records


def build_status_embed(guild: discord.Guild) -> discord.Embed:
    now = time.time()
    day = today_key()
    active_members: list[tuple[discord.Member, int]] = []
    support_today: list[tuple[discord.Member, int]] = []
    verifier_count = 0

    for member in guild.members:
        if member.bot or not is_verifier(member):
            continue
        verifier_count += 1

        today_seconds = int(support_daily_seconds.get(day, {}).get(str(member.id), 0) or 0)
        if today_seconds:
            support_today.append((member, today_seconds))

        if is_in_passing(member):
            joined_at = voice_joined_at.get(str(member.id), now)
            active_members.append((member, int(now - joined_at)))

    active_members.sort(key=lambda item: item[1], reverse=True)
    support_today.sort(key=lambda item: item[1], reverse=True)

    embed = discord.Embed(
        title="Статус саппорта",
        description="Текущая сводка по верификаторам и проходным.",
        color=EMBED_COLOR,
    )
    embed.add_field(name="Верификаторов", value=str(verifier_count), inline=True)
    embed.add_field(name="Сейчас в проходных", value=str(len(active_members)), inline=True)
    embed.add_field(name="Проходных каналов", value=str(len(config.PASSING_CHANNELS)), inline=True)
    embed.add_field(
        name="Сейчас в войсе",
        value="\n".join(f"{user_label(member)} — {format_duration(seconds)}" for member, seconds in active_members[:10])
        if active_members
        else "Пока никого.",
        inline=False,
    )
    embed.add_field(
        name="Сегодня активны",
        value="\n".join(f"{user_label(member)} — {format_duration(seconds)}" for member, seconds in support_today[:10])
        if support_today
        else "Сегодня пока нет активности.",
        inline=False,
    )
    embed.set_footer(text=f"Обновлено: {datetime.now(MSK_TZ).strftime('%H:%M %d.%m.%Y MSK')}")
    return embed


def build_support_stats_embed(member: discord.Member, period: str) -> discord.Embed:
    now = time.time()
    days = period_day_keys(period)
    verified, no_access = support_action_totals(member.id, days)
    voice_seconds = support_seconds_for_period(member, days, now)
    reviews_count = len(support_review_records(member.id, days))
    label = period_label(period)
    voice_label = "за неделю" if period == "week" else f"за {label.lower()}"

    embed = discord.Embed(
        title=f"Статистика — {user_label(member)}",
        description=(
            f"**Верификаций:** {verified}\n"
            f"**Недопусков:** {no_access}\n"
            f"**Время в войсе {voice_label}:** {format_duration(voice_seconds)}\n"
            f"**Отзывов:** {reviews_count}"
        ),
        color=EMBED_COLOR,
    )
    embed.set_thumbnail(url=review_image_url(member))

    if period == "week":
        day_lines = []
        for value, day_label in week_day_options()[1:]:
            day_seconds = support_seconds_for_day(member, value, now)
            day_verified, day_no_access = support_action_totals(member.id, [value])
            if day_seconds or day_verified or day_no_access:
                day_lines.append(
                    f"**{day_label}:** {format_duration(day_seconds)} • вер. {day_verified} • недоп. {day_no_access}"
                )
        if day_lines:
            embed.add_field(name="По дням", value="\n".join(day_lines)[:1024], inline=False)

    embed.set_footer(text=f"Обновлено: {datetime.now(MSK_TZ).strftime('%H:%M %d.%m.%Y MSK')}")
    return embed


def build_reviews_embed(member: discord.Member, period: str) -> discord.Embed:
    reviews = support_review_records(member.id, period_day_keys(period))
    embed = discord.Embed(
        title=f"Отзывы — {user_label(member)}",
        description=f"Период: **{period_label(period)}**",
        color=EMBED_COLOR,
    )
    embed.set_thumbnail(url=review_image_url(member))

    if not reviews:
        embed.add_field(name="Пока пусто", value="За этот период отзывов нет.", inline=False)
        return embed

    lines = []
    for review in reviews[:15]:
        rating = int(review.get("rating", 0) or 0)
        reviewer_name = str(review.get("reviewer_name", "unknown"))
        comment = str(review.get("comment", ""))
        timestamp = str(review.get("timestamp", ""))
        if timestamp:
            try:
                timestamp = datetime.fromisoformat(timestamp).strftime("%H:%M %d.%m.%Y")
            except ValueError:
                pass
        lines.append(f"**{rating}/5** от `{reviewer_name}` • {timestamp}\n{comment}")

    value = "\n\n".join(lines)
    if len(reviews) > 15:
        value += f"\n\nИ ещё отзывов: {len(reviews) - 15}"
    embed.add_field(name="Последние отзывы", value=value[:1024], inline=False)
    return embed


class SupportStatsSelect(discord.ui.Select):
    def __init__(self, selected_period: str):
        options = [
            discord.SelectOption(label=label, value=value, default=value == selected_period)
            for value, label in week_day_options()
        ]
        super().__init__(
            placeholder="Выберите период для детальной статистики...",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, SupportStatsView):
            await interaction.response.send_message("Не смог обновить статистику.", ephemeral=True)
            return
        await view.update_period(interaction, self.values[0])


class SupportReviewsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Посмотреть отзывы", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, SupportStatsView):
            await interaction.response.send_message("Не смог открыть отзывы.", ephemeral=True)
            return
        member = await view.get_target(interaction)
        if member is None:
            await interaction.response.send_message("Не нашёл этого участника на сервере.", ephemeral=True)
            return
        await interaction.response.send_message(embed=build_reviews_embed(member, view.selected_period), ephemeral=True)


class SupportStatsView(discord.ui.View):
    def __init__(self, target_id: int, guild_id: int, selected_period: str = "week"):
        super().__init__(timeout=300)
        self.target_id = target_id
        self.guild_id = guild_id
        self.selected_period = selected_period
        self.refresh_select()

    def refresh_select(self) -> None:
        self.clear_items()
        self.add_item(SupportStatsSelect(self.selected_period))
        self.add_item(SupportReviewsButton())

    async def get_target(self, interaction: discord.Interaction) -> discord.Member | None:
        guild = interaction.client.get_guild(self.guild_id) if interaction.client else None
        if guild is None and interaction.guild and interaction.guild.id == self.guild_id:
            guild = interaction.guild
        if guild is None:
            return None

        member = guild.get_member(self.target_id)
        if member:
            return member
        try:
            return await guild.fetch_member(self.target_id)
        except (discord.NotFound, discord.HTTPException):
            return None

    async def update_period(self, interaction: discord.Interaction, period: str) -> None:
        member = await self.get_target(interaction)
        if member is None:
            await interaction.response.send_message("Не нашёл этого участника на основном сервере.", ephemeral=True)
            return
        self.selected_period = period
        self.refresh_select()
        await interaction.response.edit_message(embed=build_support_stats_embed(member, period), view=self)


class StatusView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Обновить", style=discord.ButtonStyle.success, custom_id="mensembot:status_refresh")
    async def refresh(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("Команда работает только на сервере.", ephemeral=True)
            return
        await interaction.response.edit_message(embed=build_status_embed(interaction.guild), view=self)


async def send_verify_log(
    interaction: discord.Interaction,
    target: discord.Member,
    action_label: str,
) -> None:
    if interaction.guild is None or not config.VERIFY_LOG_CHANNEL:
        return

    channel = interaction.guild.get_channel(config.VERIFY_LOG_CHANNEL)
    if channel is None:
        return

    embed = discord.Embed(title="Верификация", color=EMBED_COLOR, timestamp=datetime.now(timezone.utc))
    embed.add_field(name="Участник", value=f"{target.mention} (`{target.id}`)", inline=False)
    embed.add_field(name="Саппорт", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
    embed.add_field(name="Действие", value=action_label, inline=False)
    await channel.send(embed=embed)


def record_support_action(member_id: int, action: str) -> None:
    add_action(member_id, action)
    save_stats()


def record_support_review(
    moderator_id: int,
    reviewer: discord.Member | discord.User,
    rating: int,
    comment: str,
) -> None:
    day = today_key()
    stats = support_action_stats.setdefault(day, {}).setdefault(
        str(moderator_id),
        {"verified": 0, "no_access": 0, "reviews": []},
    )
    reviews = stats.setdefault("reviews", [])
    if isinstance(reviews, list):
        reviews.append(
            {
                "reviewer_id": int(reviewer.id),
                "reviewer_name": user_label(reviewer),
                "rating": int(rating),
                "comment": comment,
                "timestamp": datetime.now(MSK_TZ).isoformat(),
            }
        )
    save_stats()


def local_timestamp() -> str:
    return datetime.now(MSK_TZ).strftime("%H:%M %d.%m.%Y MSK")


def build_verification_done_embed(
    target: discord.Member,
    moderator: discord.Member | discord.User,
    action: str = "verified",
    reason: str | None = None,
) -> discord.Embed:
    if action == "no_access":
        description = (
            f"{target.mention} не был допущен к серверу - {moderator.mention}\n\n"
            f"Недопуск был выдан - {local_timestamp()}\n"
            f"Причина: {reason or 'Не указана'}"
        )
    else:
        description = (
            f"{target.mention} успешно верифицирован - {moderator.mention}\n\n"
            f"Верификация была пройдена - {local_timestamp()}"
        )

    embed = discord.Embed(description=description, color=EMBED_COLOR)
    embed.set_thumbnail(url=target.display_avatar.url)
    return embed


async def disconnect_from_passing(member: discord.Member) -> str | None:
    if not is_in_passing(member):
        return None

    try:
        await member.move_to(None, reason="Verification completed")
    except discord.Forbidden:
        return "Не смог кикнуть человека из проходной. Нужен перм `Move Members`."
    except discord.HTTPException:
        return "Не смог кикнуть человека из проходной из-за ошибки Discord."

    return None


async def send_review_log(
    guild: discord.Guild | None,
    target: discord.Member | discord.User,
    moderator_id: int,
    rating: int,
    comment: str,
) -> None:
    channel_id = int(config.REVIEW_LOG_CHANNEL or 0)
    if guild is None or not channel_id:
        return

    channel = guild.get_channel(channel_id)
    if channel is None:
        try:
            channel = await guild.fetch_channel(channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return
    if channel is None or not hasattr(channel, "send"):
        return

    embed = discord.Embed(
        title="Новый отзыв о верификации",
        description=(
            f"Участник: {target.mention}\n"
            f"Саппорт: <@{moderator_id}>\n"
            f"Оценка: **{rating} баллов**\n"
            f"Отзыв: {comment}"
        ),
        color=EMBED_COLOR,
    )
    try:
        await channel.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        pass


async def send_review_to_moderator(
    client: discord.Client | None,
    target: discord.Member | discord.User,
    moderator_id: int,
    rating: int,
    comment: str,
) -> None:
    if client is None:
        return

    moderator = client.get_user(moderator_id)
    if moderator is None:
        try:
            moderator = await client.fetch_user(moderator_id)
        except (discord.NotFound, discord.HTTPException):
            return

    embed = discord.Embed(
        title="Отзыв о твоей верификации",
        description=(
            f"Участник: {target.mention}\n"
            f"Оценка: **{rating} баллов**\n"
            f"Отзыв: {comment}"
        ),
        color=EMBED_COLOR,
    )
    embed.set_thumbnail(url=review_image_url(target))

    try:
        await moderator.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        pass


class ReviewModal(discord.ui.Modal):
    def __init__(self, rating: int, moderator_id: int, guild_id: int | None):
        super().__init__(title="Отзыв")
        self.rating = rating
        self.moderator_id = moderator_id
        self.guild_id = guild_id
        self.comment = discord.ui.TextInput(
            label="Ваш отзыв",
            placeholder="Например: всё топчик",
            max_length=300,
            style=discord.TextStyle.paragraph,
            required=True,
        )
        self.add_item(self.comment)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        comment = str(self.comment.value).strip()
        embed = discord.Embed(
            title="Отзыв",
            description=(
                "Вы успешно оставили отзыв!\n"
                f"Ваш отзыв: **{self.rating} баллов**\n"
                f"`{comment}`"
            ),
            color=EMBED_COLOR,
        )
        embed.set_thumbnail(url=review_image_url(interaction.user))

        await interaction.response.edit_message(embed=embed, view=None)
        guild = interaction.client.get_guild(self.guild_id) if interaction.client and self.guild_id else None

        try:
            record_support_review(self.moderator_id, interaction.user, self.rating, comment)
        except Exception:
            logging.exception("Failed to persist support review")

        try:
            await send_review_log(guild, interaction.user, self.moderator_id, self.rating, comment)
        except Exception:
            logging.exception("Failed to send support review log")

        try:
            await send_review_to_moderator(interaction.client, interaction.user, self.moderator_id, self.rating, comment)
        except Exception:
            logging.exception("Failed to DM support moderator review")


class ReviewView(discord.ui.View):
    def __init__(self, moderator_id: int, guild_id: int | None):
        super().__init__(timeout=86400)
        self.moderator_id = moderator_id
        self.guild_id = guild_id

    async def open_review_modal(self, interaction: discord.Interaction, rating: int) -> None:
        await interaction.response.send_modal(ReviewModal(rating, self.moderator_id, self.guild_id))

    @discord.ui.button(label="1", style=discord.ButtonStyle.danger)
    async def one(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.open_review_modal(interaction, 1)

    @discord.ui.button(label="2", style=discord.ButtonStyle.danger)
    async def two(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.open_review_modal(interaction, 2)

    @discord.ui.button(label="3", style=discord.ButtonStyle.secondary)
    async def three(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.open_review_modal(interaction, 3)

    @discord.ui.button(label="4", style=discord.ButtonStyle.success)
    async def four(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.open_review_modal(interaction, 4)

    @discord.ui.button(label="5", style=discord.ButtonStyle.success)
    async def five(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.open_review_modal(interaction, 5)


async def send_review_request(
    target: discord.Member,
    moderator: discord.Member | discord.User,
    guild: discord.Guild,
) -> bool:
    embed = discord.Embed(
        title="Отзыв",
        description=(
            "Верификация пройдена.\n"
            f"Проверяющий: {moderator.mention}\n\n"
            "Оцени, пожалуйста, как прошла верификация."
        ),
        color=EMBED_COLOR,
    )
    embed.set_thumbnail(url=review_image_url(target))

    try:
        await target.send(embed=embed, view=ReviewView(moderator.id, guild.id))
    except discord.Forbidden:
        return False
    except discord.HTTPException:
        return False

    return True


def build_verify_embed(target: discord.Member, moderator: discord.Member | discord.User) -> discord.Embed:
    embed = discord.Embed(
        title="Верификация Support",
        description=f"Участник: {target.mention}\nID: `{target.id}`",
        color=EMBED_COLOR,
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="Юзер", value=user_label(target), inline=True)
    embed.add_field(name="Проверяющий", value=moderator.mention, inline=True)
    embed.add_field(
        name="Аккаунт создан",
        value=discord.utils.format_dt(target.created_at, style="F"),
        inline=False,
    )
    joined_at = target.joined_at
    embed.add_field(
        name="Зашел на сервер",
        value=discord.utils.format_dt(joined_at, style="F") if joined_at else "Неизвестно",
        inline=False,
    )
    return embed


class VerifyView(discord.ui.View):
    def __init__(self, target: discord.Member):
        super().__init__(timeout=180)
        self.target = target

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if isinstance(interaction.user, discord.Member) and interaction.guild and interaction.user.id == interaction.guild.owner_id:
            return True
        if not isinstance(interaction.user, discord.Member) or not is_verifier(interaction.user):
            await interaction.response.send_message("Недостаточно прав для верификации.", ephemeral=True)
            return False
        return True

    async def apply_result(self, interaction: discord.Interaction, role_key: str, action_key: str, label: str) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)

        role = await get_configured_role(interaction.guild, role_key)
        if role is None:
            return await interaction.response.send_message(f"Роль `{role_key}` не настроена или не найдена.", ephemeral=True)

        removable = []
        for key in ("unverify", "female", "male", "no_access"):
            configured = await get_configured_role(interaction.guild, key)
            if configured and configured in self.target.roles and configured != role:
                removable.append(configured)

        try:
            if removable:
                await self.target.remove_roles(*removable, reason=f"Verify: {label}")
            if role not in self.target.roles:
                await self.target.add_roles(role, reason=f"Verify: {label}")
        except discord.Forbidden:
            return await interaction.response.send_message("Не хватает прав Discord для изменения ролей.", ephemeral=True)
        except discord.HTTPException as exc:
            return await interaction.response.send_message(f"Discord API вернул ошибку: {exc}", ephemeral=True)

        await interaction.response.defer()

        record_support_action(interaction.user.id, action_key)
        voice_warning = await disconnect_from_passing(self.target)
        review_sent = True if action_key == "no_access" else await send_review_request(self.target, interaction.user, interaction.guild)
        done_embed = build_verification_done_embed(
            self.target,
            interaction.user,
            "no_access" if action_key == "no_access" else "verified",
        )
        await send_verify_log(interaction, self.target, label)
        await interaction.edit_original_response(content=None, embed=done_embed, view=None)
        await interaction.followup.send(
            "Готово: "
            + (
                f"{self.target.mention} не допущен."
                if action_key == "no_access"
                else f"{self.target.mention} верифицирован."
            ),
            ephemeral=True,
        )
        if voice_warning:
            await interaction.followup.send(voice_warning, ephemeral=True)
        if not review_sent and action_key != "no_access":
            await interaction.followup.send(
                "Не смог отправить отзыв в ЛС: у участника закрыты личные сообщения.",
                ephemeral=True,
            )

    @discord.ui.button(label="Мужской", style=discord.ButtonStyle.success)
    async def male(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.apply_result(interaction, "male", "verified", "мужской доступ")

    @discord.ui.button(label="Женский", style=discord.ButtonStyle.secondary)
    async def female(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.apply_result(interaction, "female", "verified", "женский доступ")

    @discord.ui.button(label="Нет доступа", style=discord.ButtonStyle.danger)
    async def no_access(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.apply_result(interaction, "no_access", "no_access", "нет доступа")


async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot:
        return

    key = str(member.id)
    now = time.time()

    if not is_verifier(member):
        if key in voice_joined_at:
            voice_joined_at.pop(key, None)
            save_stats()
        return

    if is_passing_channel(before.channel) and key in voice_joined_at:
        joined_at = voice_joined_at.pop(key)
        add_voice_seconds(member.id, int(now - joined_at))
        save_stats()

    if is_passing_channel(after.channel):
        voice_joined_at[key] = now
        save_stats()

async def setup(bot: commands.Bot):
    await init_database()
    await load_stats_db()

    @bot.tree.command(name="verify", description="Открыть панель верификации участника")
    async def verify(interaction: discord.Interaction, user: str) -> None:
# ...

        if interaction.guild is None:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)
        if interaction.guild.id != config.GUILD_ID:
            return await interaction.response.send_message(
                "Верификация доступна только на основном сервере и только в чате проходного голосового канала.",
                ephemeral=True,
            )
        is_owner = interaction.user.id == interaction.guild.owner_id
        if not is_owner:
            if not isinstance(interaction.user, discord.Member) or not is_verifier(interaction.user):
                return await interaction.response.send_message("Недостаточно прав.", ephemeral=True)
            if not is_passing_channel(interaction.channel):
                return await interaction.response.send_message(
                    "В этом чате нельзя верифицировать. Используй /verify только в чате проходного голосового канала.",
                    ephemeral=True,
                )

        target = await resolve_member(interaction, user)
        if target is None:
            return await interaction.response.send_message("Участник не найден. Укажи mention или ID.", ephemeral=True)

        await interaction.response.send_message(
            embed=build_verify_embed(target, interaction.user),
            view=VerifyView(target),
        )

    @bot.tree.command(name="status", description="Показать статистику проходных за сегодня")
    async def status(interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("Команда работает только на сервере.", ephemeral=True)
        await interaction.response.send_message(embed=build_status_embed(interaction.guild), view=StatusView(), ephemeral=True)

    @bot.tree.command(name="stats", description="Показать личную статистику саппорта")
    @app_commands.describe(user="Саппорт, статистику которого нужно посмотреть")
    async def stats(interaction: discord.Interaction, user: discord.User | None = None) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("Команда работает только на сервере.", ephemeral=True)

        main_guild = interaction.client.get_guild(config.GUILD_ID) if interaction.client else None
        if main_guild is None:
            main_guild = interaction.guild

        target_user = user or interaction.user
        member = main_guild.get_member(target_user.id)
        if member is None:
            try:
                member = await main_guild.fetch_member(target_user.id)
            except discord.NotFound:
                return await interaction.response.send_message("Не нашёл этого участника на основном сервере.", ephemeral=True)
            except discord.HTTPException:
                return await interaction.response.send_message("Discord не дал загрузить участника, попробуй ещё раз.", ephemeral=True)

        if not is_verifier(member):
            return await interaction.response.send_message(
                "Этот участник не имеет роли саппорта и не учитывается в статистике.",
                ephemeral=True,
            )

        await interaction.response.send_message(
            embed=build_support_stats_embed(member, "week"),
            view=SupportStatsView(member.id, main_guild.id),
        )

    bot.add_listener(on_voice_state_update, "on_voice_state_update")
    print("OK Verify module loaded")
