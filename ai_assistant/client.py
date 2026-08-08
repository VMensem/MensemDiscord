from __future__ import annotations

import logging

from .config import AIConfig, load_ai_config
from .database import add_message, check_rate_limit, cleanup_history, clear_history, get_config, get_history
from .providers import AIMessage, AIProviderError, AIResponse
from .providers.gemini import GeminiProvider
from .providers.openai import OpenAIProvider


PROVIDER_FACTORIES = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
}


class AIClient:
    def __init__(self, config: AIConfig | None = None):
        self.config = config or load_ai_config()
        self.provider = None
        self.startup_error: AIProviderError | None = None

        if self.config.provider == "none":
            return

        factory = PROVIDER_FACTORIES.get(self.config.provider)
        if factory is None:
            self.startup_error = AIProviderError(
                f"Неизвестный AI_PROVIDER: {self.config.provider}",
                code="invalid_provider",
            )
            return

        try:
            self.provider = factory(self.config)
        except AIProviderError as exc:
            self.startup_error = exc
        except Exception as exc:
            self.startup_error = AIProviderError(str(exc), code="provider_init_failed")

    @property
    def provider_name(self) -> str:
        if self.provider is not None:
            return self.provider.name
        return self.config.provider

    @property
    def model(self) -> str:
        if self.provider is not None:
            return self.provider.model
        if self.config.provider == "gemini":
            return self.config.gemini_model
        if self.config.provider == "openai":
            return self.config.openai_model
        return "-"

    @property
    def is_enabled(self) -> bool:
        enabled = str(get_config("enabled", "true") or "true").strip().lower()
        return self.config.provider != "none" and enabled not in {"0", "false", "no", "off"}

    @property
    def is_ready(self) -> bool:
        return self.provider is not None and self.startup_error is None

    @property
    def limit_per_hour(self) -> int:
        raw = get_config("limit_per_hour", "20")
        try:
            return max(1, int(raw or 20))
        except (TypeError, ValueError):
            return 20

    def rate_limit_ok(self, user_id: int) -> bool:
        return check_rate_limit(user_id, self.limit_per_hour)

    async def generate(self, user_id: int, prompt: str) -> AIResponse:
        if not self.is_enabled:
            raise AIProviderError("AI-ассистент отключён.", code="disabled")
        if self.startup_error is not None:
            raise self.startup_error
        if self.provider is None:
            raise AIProviderError("AI-провайдер не настроен.", code="disabled")

        cleanup_history(user_id, self.config.history_limit, self.config.history_ttl_days)
        add_message(user_id, "user", prompt)
        history_rows = get_history(user_id, limit=self.config.history_limit, ttl_days=self.config.history_ttl_days)
        messages = [AIMessage(role=row["role"], content=row["message"]) for row in history_rows]

        response = await self.provider.generate(messages, self.config.system_prompt)
        add_message(user_id, "assistant", response.text)
        cleanup_history(user_id, self.config.history_limit, self.config.history_ttl_days)

        logging.info(
            "AI response provider=%s model=%s latency_ms=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s",
            response.provider,
            response.model,
            response.latency_ms,
            response.prompt_tokens,
            response.completion_tokens,
            response.total_tokens,
        )
        return response

    def clear_history(self, user_id: int) -> None:
        clear_history(user_id)
