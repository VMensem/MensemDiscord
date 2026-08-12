import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

DEFAULT_SYSTEM_PROMPT_PATH = Path(__file__).with_name("system_prompt.txt")


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def load_system_prompt() -> str:
    env_prompt = os.getenv("AI_SYSTEM_PROMPT", "").strip()
    if env_prompt:
        return env_prompt
    if DEFAULT_SYSTEM_PROMPT_PATH.exists():
        return DEFAULT_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    return "Ты полезный Discord-ассистент сервера Mensem. Отвечай кратко, дружелюбно и по делу."


@dataclass(frozen=True)
class AIConfig:
    provider: str
    gemini_api_keys: list[str]
    gemini_model: str
    openai_api_keys: list[str]
    openai_model: str
    max_tokens: int
    temperature: float
    timeout: float
    system_prompt: str
    history_limit: int
    history_ttl_days: int


def load_ai_config() -> AIConfig:
    provider = os.getenv("AI_PROVIDER", "none").strip().lower()
    if provider not in {"gemini", "openai", "none"}:
        provider = "none"

    def get_keys(prefix: str) -> list[str]:
        keys = []
        # Support CSV list
        csv = os.getenv(f"{prefix}_API_KEYS", "").strip()
        if csv:
            keys.extend([k.strip() for k in csv.split(",") if k.strip()])
        # Support single key
        single = os.getenv(f"{prefix}_API_KEY", "").strip()
        if single and single not in keys:
            keys.append(single)
        return keys

    return AIConfig(
        provider=provider,
        gemini_api_keys=get_keys("GEMINI"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash",
        openai_api_keys=get_keys("OPENAI"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini",
        max_tokens=max(1, _int_env("AI_MAX_TOKENS", 1024)),
        temperature=max(0.0, min(2.0, _float_env("AI_TEMPERATURE", 0.7))),
        timeout=max(1.0, _float_env("AI_TIMEOUT", 30.0)),
        system_prompt=load_system_prompt(),
        history_limit=max(1, _int_env("AI_HISTORY_LIMIT", 12)),
        history_ttl_days=max(1, _int_env("AI_HISTORY_TTL_DAYS", 14)),
    )
