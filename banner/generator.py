from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import config


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if config.FONT_PATH:
        font_path = Path(config.FONT_PATH)
        if font_path.exists():
            try:
                return ImageFont.truetype(str(font_path), size)
            except Exception:
                logger.exception("Failed to load banner font from %s", font_path)

    for candidate in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue

    return ImageFont.load_default()


def _draw_text_with_glow(draw: ImageDraw.ImageDraw, position: tuple[int, int], text: str, font, fill_color, outline_color, glow_color) -> None:
    x, y = position
    for offset in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
        draw.text((x + offset[0], y + offset[1]), text, font=font, fill=glow_color)
    for offset in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        draw.text((x + offset[0], y + offset[1]), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=fill_color)


def generate_banner(stats: dict) -> str:
    background_path = Path(config.BACKGROUND_PATH)
    if not background_path.exists():
        raise FileNotFoundError(f"Banner background not found: {background_path}")

    img = Image.open(background_path).convert("RGBA")
    if img.size != config.BANNER_SIZE:
        img = img.resize(config.BANNER_SIZE)

    draw = ImageDraw.Draw(img)
    panels = {
        "members": (250, 390, 150, 50),
        "online": (250, 680, 150, 50),
        "voice": (1550, 390, 150, 50),
        "boosts": (1550, 680, 150, 50),
    }

    font = _load_font(70)
    for key, value in stats.items():
        text = str(value)
        panel = panels.get(key)
        if panel is None:
            continue

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = panel[0] + (panel[2] - text_width) // 2
        y = panel[1] + (panel[3] - text_height) // 2

        _draw_text_with_glow(
            draw,
            (x, y),
            text,
            font,
            fill_color="#FFFFFF",
            outline_color="#FF1A1A",
            glow_color="#FF1A1A55",
        )

    output_path = Path(config.TEMP_BANNER_PATH)
    img.save(output_path)
    return str(output_path)
