from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Iterable


POSITIONS = (
    "Support",
    "Moderator",
    "EventMod",
    "CloseMod",
    "TribuneMod",
    "ContentMaker",
    "Helper",
)

POSITION_DESCRIPTIONS = {
    "Support": "Помощь пользователям, ответы на вопросы и первичная поддержка.",
    "Moderator": "Контроль порядка на сервере и работа с нарушениями.",
    "EventMod": "Организация и сопровождение ивентов.",
    "CloseMod": "Работа с закрытыми комнатами, лобби и приватными зонами.",
    "TribuneMod": "Проведение активности и контроль трибуны.",
    "ContentMaker": "Создание контента, оформление и креативные задачи.",
    "Helper": "Общая помощь команде и поддержка рабочих процессов.",
}


@dataclass(frozen=True, slots=True)
class StaffPositionConfig:
    name: str
    role_env: str
    channel_env: str
    description: str


POSITION_CONFIGS = {
    position: StaffPositionConfig(
        name=position,
        role_env=f"{position.upper()}_ROLE_ID",
        channel_env=f"STAFF_{position.upper()}_APPLICATION_CHANNEL_ID",
        description=POSITION_DESCRIPTIONS[position],
    )
    for position in POSITIONS
}


def get_env_int(key: str, default: int = 0) -> int:
    raw = os.getenv(key, "").strip()
    return int(raw) if raw.isdigit() else default


def normalize_position(position: str) -> str | None:
    position = position.strip()
    for name in POSITIONS:
        if name.lower() == position.lower():
            return name
    return None


def get_position_config(position: str) -> StaffPositionConfig | None:
    normalized = normalize_position(position)
    if normalized is None:
        return None
    return POSITION_CONFIGS[normalized]


def iter_position_configs() -> Iterable[StaffPositionConfig]:
    for position in POSITIONS:
        yield POSITION_CONFIGS[position]


def get_staff_role_id(position: str) -> int:
    config = get_position_config(position)
    if config is None:
        return 0
    return get_env_int(config.role_env)


def get_application_channel_id(position: str) -> int:
    config = get_position_config(position)
    if config is None:
        return 0

    channel_id = get_env_int(config.channel_env)
    if channel_id:
        return channel_id

    # Backward-compatible fallback for older .env layouts.
    return get_env_int("STAFF_APPLICATION_CHANNEL_ID")


def configured_staff_role_ids() -> set[int]:
    role_ids: set[int] = set()
    for config in iter_position_configs():
        role_id = get_env_int(config.role_env)
        if role_id:
            role_ids.add(role_id)
    return role_ids


def is_staff_reviewer(member) -> bool:
    if member.guild_permissions.administrator:
        return True

    role_ids = configured_staff_role_ids()
    return any(role.id in role_ids for role in getattr(member, "roles", []))
