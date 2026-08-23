import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "LOG_CHANNEL": int(os.getenv("CLANS_LOG_CHANNEL_ID", 0)),
    "CREATE_COST": int(os.getenv("CLANS_CREATE_COST", 1000)),
    "MAX_MEMBERS": int(os.getenv("CLANS_MAX_MEMBERS", 20)),
    "EMBED_COLOR": int(os.getenv("CLANS_EMBED_COLOR", "#C1121F").lstrip("#"), 16),
    "FOOTER": os.getenv("CLANS_FOOTER", "Mensem Clans System")
}
