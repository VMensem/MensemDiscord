import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "START_BALANCE": int(os.getenv("ECONOMY_START_BALANCE", 1000)),
    "DAILY_REWARD": int(os.getenv("ECONOMY_DAILY_REWARD", 500)),
    "TAX_PERCENT": int(os.getenv("ECONOMY_TAX_PERCENT", 5)),
    "EMBED_COLOR": int(os.getenv("ECONOMY_EMBED_COLOR", "#C1121F").lstrip("#"), 16),
    "FOOTER": os.getenv("ECONOMY_FOOTER", "Mensem Economy System")
}
