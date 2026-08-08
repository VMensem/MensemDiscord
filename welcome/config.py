from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def get_env_int(key: str, default: int = 0) -> int:
    raw = os.getenv(key, "").strip()
    return int(raw) if raw.isdigit() else default


WELCOME_CHANNEL_ID = get_env_int("WELCOME_CHANNEL_ID", 0)
WELCOME_BACKGROUND_PATH = os.getenv("WELCOME_BACKGROUND_PATH", "").strip() or str(BASE_DIR / "assets" / "background.png")
WELCOME_FONT_PATH = os.getenv("WELCOME_FONT_PATH", "").strip()
