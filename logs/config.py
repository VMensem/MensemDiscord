import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")


def get_env_int(key: str, default: int = 0) -> int:
    raw = os.getenv(key, "").strip()
    return int(raw) if raw.isdigit() else default


LEGACY_LOG_CHANNEL_ID = get_env_int("LOG_CHANNEL_ID", 1524022765382799503)

LOG_MEMBERS_CHANNEL_ID = get_env_int("LOG_MEMBERS_CHANNEL_ID", LEGACY_LOG_CHANNEL_ID)
LOG_ROLES_CHANNEL_ID = get_env_int("LOG_ROLES_CHANNEL_ID", LEGACY_LOG_CHANNEL_ID)
LOG_CHANNELS_CHANNEL_ID = get_env_int("LOG_CHANNELS_CHANNEL_ID", LEGACY_LOG_CHANNEL_ID)
LOG_VOICE_CHANNEL_ID = get_env_int("LOG_VOICE_CHANNEL_ID", LEGACY_LOG_CHANNEL_ID)
LOG_MESSAGES_CHANNEL_ID = get_env_int("LOG_MESSAGES_CHANNEL_ID", LEGACY_LOG_CHANNEL_ID)
LOG_MODERATION_CHANNEL_ID = get_env_int("LOG_MODERATION_CHANNEL_ID", LEGACY_LOG_CHANNEL_ID)
LOG_MISC_CHANNEL_ID = get_env_int("LOG_MISC_CHANNEL_ID", LEGACY_LOG_CHANNEL_ID)

# Backward-compatible alias for older imports.
LOG_CHANNEL = LOG_MISC_CHANNEL_ID
