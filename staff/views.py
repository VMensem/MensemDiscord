from __future__ import annotations

import json
from typing import Any

import discord

from .config import (
    get_application_channel_id,
    get_position_config,
    get_staff_role_id,
    is_staff_reviewer,
    iter_position_configs,
    normalize_position,
)
from .database import (
    StaffApplicationConflict,
    StaffApplicationNotFound,
    StaffApplicationStateError,
    create_application,
    cancel_application,
    get_application,
    list_open_applications,
    mark_application_review_state,
    set_application_message,
)


def _shorten(value: str, limit: int = 1024) -> str:
    value = value.strip() or "—"
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _parse_answers(answers: Any) -> list[tuple[str, str]]:
    if isinstance(answers, dict):
        items = list(answers.items())
    else:
        raw = str(answers or "").strip()
        if not raw:
            return []
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            return [("Ответы", raw)]
        if isinstance(decoded, dict):
            items = list(decoded.items())
        else:
            return [("Ответы", raw)]

    return [(str(key), str(value)) for key, value in items]


def build_application_embed(application: dict[str, Any]) -> discord.Embed:
    status = application["status"]
    status_labels = {
        "pending": "На рассмотрении",
        "claimed": "Взята в работу",
        "accepted": "Принята",
        "rejected": "Отклонена",
    }
    colors = {
        "pending": discord.Color.gold(),
        "claimed": discord.Color.blurple(),
        "accepted": discord.Color.green(),
        "rejected": discord.Color.red(),
    }

    embed = discord.Embed(
        title=f"Заявка #{application['application_id']}",
        description=f"Позиция: **{application['position']}**",
        color=colors.get(status, discord.Color.gold()),
    )
    embed.add_field(name="Кандидат", value=f"<@{application['user_id']}>", inline=True)
    embed.add_field(name="Статус", value=status_labels.get(status, status), inline=True)
    reviewer_id = application.get("reviewer_id")
    embed.add_field(name="Ревьюер", value=f"<@{reviewer_id}>" if reviewer_id else "—", inline=True)

    if application.get("rejection_reason"):
        embed.add_field(
            name="Причина отклонения",
            value=_shorten(str(application["rejection_reason"]), 1024),
            inline=False,
        )

    answers = _parse_answers(application.get("answers"))
    if answers:
        for index, (question, answer) in enumerate(answers, start=1):
            field_name = _shorten(f"{index}. {question}", 256)
            embed.add_field(name=field_name, value=_shorten(str(answer)), inline=False)

    embed.set_footer(text="Mensem Staff Recruitment")
    return embed


def build_setup_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Набор в Staff",
        description=(
            "Выбери подходящую ветку и заполни короткую анкету.\n\n"
            "Заявка уйдёт сразу в отдельный канал для выбранного направления."
        ),
        color=discord.Color.red(),
    )
    embed.add_field(
        name="Как это работает",
        value="1. Выбираешь позицию\n2. Заполняешь анкету\n3. Ждёшь решения команды",
        inline=False,
    )
    return embed


class StaffApplicationModal(discord.ui.Modal):
    def __init__(self, position: str):
        normalized = normalize_position(position)
        if normalized is None:
            raise ValueError(f"Unsupported staff position: {position}")

        self.position = normalized
        title = f"Заявка: {normalized}"
        super().__init__(title=title)

        self.name_input = discord.ui.TextInput(
            label="Как к тебе обращаться?",
            placeholder="Имя или никнейм",
            max_length=64,
        )
        self.age_input = discord.ui.TextInput(
            label="Возраст",
            placeholder="Сколько тебе лет?",
            max_length=32,
        )
        self.timezone_input = discord.ui.TextInput(
            label="Часовой пояс",
            placeholder="Например: GMT+3",
            max_length=32,
        )
        self.experience_input = discord.ui.TextInput(
            label="Опыт",
            placeholder="Что уже делал на похожих ролях?",
            style=discord.TextStyle.paragraph,
            max_length=1000,
        )
        self.motivation_input = discord.ui.TextInput(
            label="Почему хочешь в Staff?",
            placeholder="Коротко о мотивации",
            style=discord.TextStyle.paragraph,
            max_length=1000,
        )

        self.add_item(self.name_input)
        self.add_item(self.age_input)
        self.add_item(self.timezone_input)
        self.add_item(self.experience_input)
        self.add_item(self.motivation_input)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Ошибка",
                    description="Заявка доступна только на сервере.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        config = get_position_config(self.position)
        if config is None:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Ошибка",
                    description="Эта позиция сейчас недоступна.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        channel_id = get_application_channel_id(self.position)
        if not channel_id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="Канал не настроен",
                    description=(
                        f"Для ветки **{self.position}** не указан канал заявок.\n"
                        "Сообщи администратору, чтобы он добавил нужный `STAFF_..._APPLICATION_CHANNEL_ID` в `.env`."
                    ),
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True, thinking=True)

        target_channel = interaction.guild.get_channel(channel_id)
        if target_channel is None:
            try:
                target_channel = await interaction.guild.fetch_channel(channel_id)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                target_channel = None

        if target_channel is None or not hasattr(target_channel, "send"):
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Канал недоступен",
                    description=(
                        f"Канал для ветки **{self.position}** не найден или недоступен для отправки сообщений."
                    ),
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        answers = {
            self.name_input.label: self.name_input.value,
            self.age_input.label: self.age_input.value,
            self.timezone_input.label: self.timezone_input.value,
            self.experience_input.label: self.experience_input.value,
            self.motivation_input.label: self.motivation_input.value,
        }

        try:
            application = await create_application(
                interaction.user.id,
                interaction.guild.id,
                self.position,
                answers,
            )
        except StaffApplicationConflict as exc:
            existing = exc.application or await self._load_existing_application(interaction.user.id, interaction.guild.id)
            embed = discord.Embed(
                title="Заявка уже существует",
                description=f"У тебя уже есть активная заявка на **{self.position}**.",
                color=discord.Color.orange(),
            )
            if existing is not None:
                embed.add_field(name="ID", value=f"#{existing['application_id']}", inline=True)
                embed.add_field(name="Статус", value=str(existing.get("status", "pending")), inline=True)
            return await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Не удалось создать заявку",
                    description="Произошла ошибка при сохранении заявки. Попробуй ещё раз чуть позже.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        view = StaffApplicationManagementView(application)
        try:
            message = await target_channel.send(
                embed=build_application_embed(application),
                view=view,
            )
        except (discord.Forbidden, discord.HTTPException):
            await cancel_application(application["application_id"], reason="channel_send_failed")
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Не удалось отправить заявку",
                    description="Заявка сохранена не была, потому что Discord не принял сообщение в канал ветки.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        try:
            await set_application_message(application["application_id"], target_channel.id, message.id)
        except Exception:
            pass

        await interaction.followup.send(
            embed=discord.Embed(
                title="Заявка отправлена",
                description=f"Заявка на **{self.position}** ушла в <#{target_channel.id}>.",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

    async def _load_existing_application(self, user_id: int, guild_id: int) -> dict[str, Any] | None:
        # This is only used as a fallback if the conflict object did not carry a row.
        from .database import get_active_application

        return await get_active_application(user_id, guild_id, self.position)


class StaffApplicationManagementView(discord.ui.View):
    def __init__(self, application: dict[str, Any]):
        super().__init__(timeout=None)
        self.application_id = int(application["application_id"])
        self.position = str(application["position"])
        self.status = str(application.get("status", "pending"))
        self.reviewer_id = application.get("reviewer_id")
        self._build_buttons()

    def _button(self, label: str, style: discord.ButtonStyle, action: str, disabled: bool = False) -> discord.ui.Button:
        button = discord.ui.Button(
            label=label,
            style=style,
            custom_id=f"staff_application:{self.application_id}:{action}",
            disabled=disabled,
        )
        return button

    def _build_buttons(self) -> None:
        final_state = self.status in {"accepted", "rejected"}
        claim_disabled = self.status == "claimed" or final_state

        claim = self._button("Взять", discord.ButtonStyle.primary, "claim", disabled=claim_disabled)
        accept = self._button("Принять", discord.ButtonStyle.success, "accept", disabled=final_state)
        reject = self._button("Отклонить", discord.ButtonStyle.danger, "reject", disabled=final_state)

        claim.callback = self.claim  # type: ignore[assignment]
        accept.callback = self.accept  # type: ignore[assignment]
        reject.callback = self.reject  # type: ignore[assignment]

        self.add_item(claim)
        self.add_item(accept)
        self.add_item(reject)

    async def _ensure_permission(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            await interaction.response.send_message("Эта кнопка работает только на сервере.", ephemeral=True)
            return False

        member = interaction.user
        if not isinstance(member, discord.Member):
            await interaction.response.send_message("Не удалось определить участника сервера.", ephemeral=True)
            return False

        if not is_staff_reviewer(member):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Нет доступа",
                    description="Эта кнопка доступна только администраторам и staff-ролям.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return False

        return True

    async def _load_application(self) -> dict[str, Any]:
        application = await get_application(self.application_id)
        if application is None:
            raise StaffApplicationNotFound("application_not_found")
        return application

    async def _edit_message(self, interaction: discord.Interaction, application: dict[str, Any]) -> None:
        view = StaffApplicationManagementView(application)
        try:
            await interaction.message.edit(embed=build_application_embed(application), view=view)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

    async def _dm_applicant(self, interaction: discord.Interaction, application: dict[str, Any], accepted: bool, note: str | None = None) -> None:
        user = interaction.guild.get_member(application["user_id"]) if interaction.guild else None
        if user is None:
            try:
                user = await interaction.client.fetch_user(application["user_id"])
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                user = None

        if user is None:
            return

        color = discord.Color.green() if accepted else discord.Color.red()
        title = "Заявка одобрена" if accepted else "Заявка отклонена"
        description = f"Твоя заявка на **{application['position']}** была {'одобрена' if accepted else 'отклонена'}."
        embed = discord.Embed(title=title, description=description, color=color)
        if note:
            embed.add_field(name="Комментарий", value=_shorten(note, 1024), inline=False)
        try:
            await user.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    async def _grant_role(self, interaction: discord.Interaction, application: dict[str, Any]) -> str | None:
        role_id = get_staff_role_id(application["position"])
        if not role_id:
            return "Для этой позиции не настроена роль."

        role = interaction.guild.get_role(role_id) if interaction.guild else None
        if role is None:
            return "Роль для этой позиции не найдена на сервере."

        member = interaction.guild.get_member(application["user_id"]) if interaction.guild else None
        if member is None:
            try:
                member = await interaction.guild.fetch_member(application["user_id"]) if interaction.guild else None
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                member = None

        if member is None:
            return "Кандидат уже не состоит на сервере."

        try:
            await member.add_roles(role, reason=f"Staff application #{self.application_id} accepted")
        except (discord.Forbidden, discord.HTTPException):
            return "Не удалось выдать роль из-за прав или ошибки Discord."
        return None

    async def _handle_review(self, interaction: discord.Interaction, action: str) -> None:
        if not await self._ensure_permission(interaction):
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            application = await self._load_application()
        except StaffApplicationNotFound:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Заявка не найдена",
                    description="Похоже, эта заявка уже удалена или была перемещена.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        try:
            updated = await mark_application_review_state(
                self.application_id,
                reviewer_id=interaction.user.id,
                status=action,
            )
        except StaffApplicationStateError as exc:
            current = exc.application or application
            if exc.args and exc.args[0] == "application_claimed_by_other":
                message = "Эту заявку уже взял другой сотрудник."
            elif exc.args and exc.args[0] == "application_already_closed":
                message = "Эта заявка уже закрыта."
            else:
                message = "Не удалось изменить состояние заявки."
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Операция отклонена",
                    description=message,
                    color=discord.Color.orange(),
                ),
                ephemeral=True,
            )
        except Exception:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Ошибка",
                    description="Не удалось обновить заявку. Попробуй ещё раз.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        await self._edit_message(interaction, updated)
        await interaction.followup.send(
            embed=discord.Embed(
                title="Готово",
                description=f"Заявка #{self.application_id} обновлена: **{updated['status']}**.",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

    async def claim(self, interaction: discord.Interaction):
        if not await self._ensure_permission(interaction):
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            updated = await mark_application_review_state(
                self.application_id,
                reviewer_id=interaction.user.id,
                status="claimed",
            )
        except StaffApplicationStateError as exc:
            if exc.args and exc.args[0] == "application_claimed_by_other":
                message = "Эту заявку уже взял другой сотрудник."
            elif exc.args and exc.args[0] == "application_already_closed":
                message = "Эта заявка уже закрыта."
            else:
                message = "Не удалось взять заявку в работу."
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Не удалось взять",
                    description=message,
                    color=discord.Color.orange(),
                ),
                ephemeral=True,
            )
        except Exception:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Ошибка",
                    description="Не удалось обновить заявку. Попробуй ещё раз.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        await self._edit_message(interaction, updated)
        await interaction.followup.send(
            embed=discord.Embed(
                title="Заявка взята",
                description=f"Заявка #{self.application_id} теперь в работе у тебя.",
                color=discord.Color.blurple(),
            ),
            ephemeral=True,
        )

    async def accept(self, interaction: discord.Interaction):
        if not await self._ensure_permission(interaction):
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            updated = await mark_application_review_state(
                self.application_id,
                reviewer_id=interaction.user.id,
                status="accepted",
            )
        except StaffApplicationStateError as exc:
            if exc.args and exc.args[0] == "application_claimed_by_other":
                message = "Эту заявку уже взял другой сотрудник."
            elif exc.args and exc.args[0] == "application_already_closed":
                message = "Эта заявка уже закрыта."
            else:
                message = "Не удалось принять заявку."
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Не удалось принять",
                    description=message,
                    color=discord.Color.orange(),
                ),
                ephemeral=True,
            )
        except Exception:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Ошибка",
                    description="Не удалось обновить заявку. Попробуй ещё раз.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        role_warning = await self._grant_role(interaction, updated)
        await self._dm_applicant(interaction, updated, accepted=True, note=role_warning)
        await self._edit_message(interaction, updated)

        description = f"Заявка #{self.application_id} принята."
        if role_warning:
            description += f"\n\n{role_warning}"
        await interaction.followup.send(
            embed=discord.Embed(
                title="Заявка принята",
                description=description,
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

    async def reject(self, interaction: discord.Interaction):
        if not await self._ensure_permission(interaction):
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            updated = await mark_application_review_state(
                self.application_id,
                reviewer_id=interaction.user.id,
                status="rejected",
            )
        except StaffApplicationStateError as exc:
            if exc.args and exc.args[0] == "application_claimed_by_other":
                message = "Эту заявку уже взял другой сотрудник."
            elif exc.args and exc.args[0] == "application_already_closed":
                message = "Эта заявка уже закрыта."
            else:
                message = "Не удалось отклонить заявку."
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Не удалось отклонить",
                    description=message,
                    color=discord.Color.orange(),
                ),
                ephemeral=True,
            )
        except Exception:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Ошибка",
                    description="Не удалось обновить заявку. Попробуй ещё раз.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        await self._dm_applicant(interaction, updated, accepted=False)
        await self._edit_message(interaction, updated)
        await interaction.followup.send(
            embed=discord.Embed(
                title="Заявка отклонена",
                description=f"Заявка #{self.application_id} отклонена.",
                color=discord.Color.red(),
            ),
            ephemeral=True,
        )


class PositionSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=config.name, description=config.description)
            for config in iter_position_configs()
        ]
        super().__init__(
            placeholder="Выберите должность",
            options=options,
            custom_id="staff_position_select",
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(StaffApplicationModal(self.values[0]))


class StaffRecruitmentPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PositionSelect())


async def register_open_application_views(bot: discord.Client) -> None:
    for application in await list_open_applications():
        bot.add_view(StaffApplicationManagementView(application))
