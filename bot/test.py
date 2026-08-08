from pathlib import Path

ROOT = Path("MensemBots")

folders = [
    "voice",
    "voice/private",
    "voice/personal",
    "voice/love",
    "voice/interviews",
    "voice/reports",
    "voice/utils",
    "voice/data",
]

files = {
    ".env": "",
    "requirements.txt": "",

    "voice.py": "",

    "voice/__init__.py": "",
    "voice/bot.py": "",
    "voice/config.py": "",
    "voice/database.py": "",
    "voice/manager.py": "",

    "voice/private/__init__.py": "",
    "voice/private/private.py": "",

    "voice/personal/__init__.py": "",
    "voice/personal/personal.py": "",

    "voice/love/__init__.py": "",
    "voice/love/love.py": "",

    "voice/interviews/__init__.py": "",
    "voice/interviews/interviews.py": "",

    "voice/reports/__init__.py": "",
    "voice/reports/reports.py": "",

    "voice/utils/__init__.py": "",
    "voice/utils/channels.py": "",
    "voice/utils/permissions.py": "",
    "voice/utils/logger.py": "",

    "voice/data/.gitkeep": "",
}

ROOT.mkdir(exist_ok=True)

for folder in folders:
    (ROOT / folder).mkdir(parents=True, exist_ok=True)

for file, content in files.items():
    path = ROOT / file
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        path.write_text(content, encoding="utf-8")

print("=" * 50)
print("✅ Структура проекта успешно создана!")
print("=" * 50)