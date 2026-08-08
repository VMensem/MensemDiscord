from __future__ import annotations

import io
from pathlib import Path

import aiohttp
from PIL import Image, ImageDraw, ImageFont

from . import config


async def generate_welcome(member):
    background_path = Path(config.WELCOME_BACKGROUND_PATH)
    background = Image.open(background_path).convert("RGBA")

    async with aiohttp.ClientSession() as session:
        async with session.get(member.display_avatar.url) as response:
            avatar_bytes = await response.read()

    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((1000, 1000))
    mask = Image.new("L", (1000, 1000), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, 1000, 1000), fill=255)
    background.paste(avatar, (200, 30), mask)

    draw = ImageDraw.Draw(background)
    font = None
    if config.WELCOME_FONT_PATH:
        font_path = Path(config.WELCOME_FONT_PATH)
        if font_path.exists():
            try:
                font = ImageFont.truetype(str(font_path), 60)
            except Exception:
                font = None
    if font is None:
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except Exception:
            font = ImageFont.load_default()

    draw.text((500, 830), "Добро пожаловать!", font=font, fill="white")
    draw.text((500, 910), member.display_name, font=font, fill=(150, 150, 255))

    buffer = io.BytesIO()
    background.save(buffer, "PNG")
    buffer.seek(0)
    return buffer
