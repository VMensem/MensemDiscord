from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


def get_env_int(key: str, default: int = 0) -> int:
    raw = os.getenv(key, "").strip()
    return int(raw) if raw.isdigit() else default


def get_env_bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key, "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return default


BANNER_ENABLED = get_env_bool("BANNER_ENABLED", True)
BANNER_DEPLOY_MODE = get_env_bool("BANNER_DEPLOY_MODE", True)
BANNER_DEBUG_MODE = get_env_bool("BANNER_DEBUG_MODE", False)
BANNER_UPDATE_INTERVAL_SECONDS = max(30, get_env_int("BANNER_UPDATE_INTERVAL_SECONDS", 60))
BANNER_LOG_CHANNEL_ID = get_env_int("BANNER_LOG_CHANNEL_ID", get_env_int("BANNER_LOG_CHANNEL", 0))
BANNER_DEBUG_CHANNEL_ID = get_env_int("BANNER_DEBUG_CHANNEL_ID", 0)

BACKGROUND_PATH = os.getenv("BANNER_BACKGROUND_PATH", "").strip() or str(BASE_DIR.parent / "banner_background.png")
FONT_PATH = os.getenv("BANNER_FONT_PATH", "").strip()
TEMP_BANNER_PATH = str(BASE_DIR / "temp_banner.png")
BANNER_SIZE = (1920, 1080)
