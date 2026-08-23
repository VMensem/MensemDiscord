import os

from dotenv import load_dotenv


load_dotenv()


TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))

PRIVATE_TRIGGER_ID = int(os.getenv("PRIVATE_TRIGGER_ID", 0))
PERSONAL_TRIGGER_ID = int(os.getenv("PERSONAL_TRIGGER_ID", 0))
LOVE_TRIGGER_ID = int(os.getenv("LOVE_TRIGGER_ID", 0))
SOBES_TRIGGER_ID = int(os.getenv("SOBES_TRIGGER_ID", 0))
REPORT_TRIGGER_ID = int(os.getenv("REPORT_TRIGGER_ID", 0))

PRIVATE_CATEGORY_ID = int(os.getenv("PRIVATE_CATEGORY_ID", 0))
PERSONAL_CATEGORY_ID = int(os.getenv("PERSONAL_CATEGORY_ID", 0))
LOVE_CATEGORY_ID = int(os.getenv("LOVE_CATEGORY_ID", 0))
SOBES_CATEGORY_ID = int(os.getenv("SOBES_CATEGORY_ID", 0))
REPORT_CATEGORY_ID = int(os.getenv("REPORT_CATEGORY_ID", 0))

# DATABASE path removed in favor of PostgreSQL


DELETE_DELAY = 5
DEFAULT_BITRATE = None
DEFAULT_USER_LIMIT = None

PRIVATE_PREFIX = "🎤・"
PERSONAL_PREFIX = "👤・"
LOVE_PREFIX = "💖・"
SOBES_PREFIX = "🎓・"
REPORT_PREFIX = "📋・"
