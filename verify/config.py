from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class Config:
    TOKEN = os.getenv("TOKEN")
    GUILD_ID = int(os.getenv("GUILD_ID", 0))

    ROLES = {
        "unverify": int(os.getenv("VERIFY_ROLE_UNVERIFY", 0)),
        "female": int(os.getenv("VERIFY_ROLE_FEMALE", 0)),
        "male": int(os.getenv("VERIFY_ROLE_MALE", 0)),
        "no_access": int(os.getenv("VERIFY_ROLE_NO_ACCESS", 0)),
    }

    PASSING_CHANNELS = [int(x.strip()) for x in os.getenv("VERIFY_PASSING_CHANNELS", "").split(",") if x.strip()]
    VERIFIER_ROLES = [int(x.strip()) for x in os.getenv("VERIFY_VERIFIER_ROLES", "").split(",") if x.strip()]
    REVIEW_LOG_CHANNEL = int(os.getenv("VERIFY_REVIEW_LOG_CHANNEL", 0))
    STAFF_GUILD = int(os.getenv("VERIFY_STAFF_GUILD", 0))
    VERIFY_LOG_CHANNEL = int(os.getenv("VERIFY_LOG_CHANNEL", 0))
    DAILY_REPORT_CHANNEL = int(os.getenv("VERIFY_DAILY_REPORT_CHANNEL", 0))
    REVIEW_IMAGE = os.getenv("VERIFY_REVIEW_IMAGE", "")

config = Config()
