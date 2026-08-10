from core.database import db_manager
from typing import Any, Dict

class StaffApplicationConflict(Exception):
    def __init__(self, message, application=None):
        super().__init__(message)
        self.application = application

async def init_db():
    pass

async def create_application(user_id: int, guild_id: int, position: str, answers: Any) -> dict[str, Any]:
    # Placeholder
    return {}

async def get_application(application_id: int) -> dict[str, Any] | None:
    return None
