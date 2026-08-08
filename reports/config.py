import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "MANAGER_ROLE": int(os.getenv("REPORT_MANAGER_ROLE_ID", 0)),
    "STAFF_ROLES": [int(i) for i in os.getenv("REPORT_STAFF_ROLE_IDS", "").split(",") if i],
    "CATEGORY": int(os.getenv("REPORT_CATEGORY_ID", 0)),
    "LOG_CHANNEL": int(os.getenv("REPORT_LOG_CHANNEL_ID", 0)),
    "EMBED_COLOR": int(os.getenv("REPORT_EMBED_COLOR", "#C1121F").lstrip("#"), 16),
}
