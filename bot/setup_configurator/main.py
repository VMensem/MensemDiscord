import discord
from .scanner import scan_guild
from .env_manager import append_to_env
from .report import generate_report

async def run_setup(guild: discord.Guild):
    data = await scan_guild(guild)
    
    # Собираем всё в плоский словарь для записи в id.txt
    all_data = {}
    
    for category, items in data.items():
        for name, id in items.items():
            # Формируем имя ключа, например: CHANNEL_WELCOME_ID
            safe_name = name.upper().replace("-", "_").replace(" ", "_")
            key = f"{category.upper().rstrip('S')}_{safe_name}_ID"
            all_data[key] = id
    
    append_to_env(all_data)
    print(f"✅ Setup complete. Found {len(all_data)} items. Check id.txt in root folder.")
