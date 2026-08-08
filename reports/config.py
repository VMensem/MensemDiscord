import os
from dotenv import load_dotenv

load_dotenv()


def _first_int_env(*names: str, default: int = 0) -> int:
    for name in names:
        raw = os.getenv(name, '').strip()
        if not raw:
            continue
        candidate = raw.split(',')[0].strip()
        if candidate.isdigit():
            return int(candidate)
    return default


CONFIG = {
    'MANAGER_ROLE': int(os.getenv('REPORT_MANAGER_ROLE_ID', 0)),
    'STAFF_ROLES': [int(i) for i in os.getenv('REPORT_STAFF_ROLE_IDS', '').split(',') if i],
    'CATEGORY': _first_int_env('REPORT_CATEGORY_IDS', 'REPORT_CATEGORY_ID', default=0),
    'LOG_CHANNEL': int(os.getenv('REPORT_LOG_CHANNEL_ID', 0)),
    'EMBED_COLOR': int(os.getenv('REPORT_EMBED_COLOR', '#C1121F').lstrip('#'), 16),
}
