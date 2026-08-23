import os
from dotenv import load_dotenv

load_dotenv()

def get_env(key, default=None):
    return os.getenv(key, default)

CONFIG = {
    "MANAGER_ROLE": int(get_env("EVENT_MANAGER_ROLE_ID", 0)),
    "STAFF_ROLES": [int(i) for i in get_env("EVENT_STAFF_ROLE_IDS", "").split(",") if i],
    "CATEGORY": int(get_env("EVENT_CATEGORY_ID", 0)),
    "LOG_CHANNEL": int(get_env("EVENT_LOG_CHANNEL_ID", 0)),
    "EMBED_COLOR": int(get_env("EVENT_EMBED_COLOR", "#C1121F").lstrip("#"), 16),
}
