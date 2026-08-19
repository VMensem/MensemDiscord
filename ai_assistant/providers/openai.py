from __future__ import annotations

import time

from ..config import AIConfig
from .base import AIMessage, AIProviderError, AIResponse


class OpenAIProvider:
    name = "openai"

    def __init__(self, config: AIConfig):
        self.model = config.openai_model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature

        if not config.openai_api_keys:
            raise AIProviderError("OPENAI_API_KEY не указан.", code="missing_api_key")

        try:
            from openai import AsyncOpenAI
        except Exception as exc:
            raise AIProviderError("Не установлен официальный OpenAI SDK `openai`.", code="missing_sdk") from exc

        self._openai_errors = self._load_error_types()
        self.client = AsyncOpenAI(api_key=config.openai_api_keys[0], timeout=config.timeout)

    async def generate(self, messages: list[AIMessage], system_prompt: str) -> AIResponse:
        payload = [{"role": "system", "content": system_prompt}]
        payload.extend({"role": message.role, "content": message.content} for message in messages)

        started = time.perf_counter()
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=payload,
                temperature=self.temperature,
                max_completion_tokens=self.max_tokens,
            )
        except Exception as exc:
            code = self._classify_error(exc)
            raise AIProviderError(self._friendly_error(code), code=code, retryable=code in {"rate_limited", "timeout", "network"}) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        text = (response.choices[0].message.content or "").strip() if response.choices else ""
        if not text:
            raise AIProviderError("OpenAI вернул пустой ответ.", code="empty_response", retryable=True)

        usage = getattr(response, "usage", None)
        return AIResponse(
            text=text,
            provider=self.name,
            model=self.model,
            latency_ms=latency_ms,
            prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
            completion_tokens=getattr(usage, "completion_tokens", None) if usage else None,
            total_tokens=getattr(usage, "total_tokens", None) if usage else None,
        )

    def _load_error_types(self) -> dict[str, type[Exception]]:
        try:
            import openai

            return {
                "auth": openai.AuthenticationError,
                "rate_limited": openai.RateLimitError,
                "timeout": openai.APITimeoutError,
                "network": openai.APIConnectionError,
                "status": openai.APIStatusError,
            }
        except Exception:
            return {}

    def _classify_error(self, exc: Exception) -> str:
        for code, error_type in self._openai_errors.items():
            if isinstance(exc, error_type):
                return code
        text = str(exc).lower()
        if "api key" in text or "authentication" in text:
            return "auth"
        if "rate" in text or "429" in text:
            return "rate_limited"
        if "timeout" in text:
            return "timeout"
        if "connection" in text or "network" in text:
            return "network"
        return "provider_error"

    def _friendly_error(self, code: str) -> str:
        return {
            "auth": "OpenAI API ключ неверный или не имеет доступа.",
            "rate_limited": "OpenAI временно ограничил запросы или квоту.",
            "timeout": "OpenAI не ответил за отведённое время.",
            "network": "Не удалось подключиться к OpenAI API.",
            "status": "OpenAI API вернул ошибку статуса.",
        }.get(code, "OpenAI API временно недоступен.")
