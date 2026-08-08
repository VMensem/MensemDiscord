from __future__ import annotations

import asyncio
import time

from ..config import AIConfig
from .base import AIMessage, AIProviderError, AIResponse


class GeminiProvider:
    name = "gemini"

    def __init__(self, config: AIConfig):
        self.model = config.gemini_model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
        self.timeout = config.timeout

        if not config.gemini_api_key:
            raise AIProviderError("GEMINI_API_KEY не указан.", code="missing_api_key")

        try:
            from google import genai
            from google.genai import types
        except Exception as exc:
            raise AIProviderError("Не установлен официальный Gemini SDK `google-genai`.", code="missing_sdk") from exc

        self._types = types
        self.client = genai.Client(api_key=config.gemini_api_key)

    async def generate(self, messages: list[AIMessage], system_prompt: str) -> AIResponse:
        prompt = self._build_prompt(messages)
        config = self._types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
        )

        started = time.perf_counter()
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model,
                    contents=prompt,
                    config=config,
                ),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError as exc:
            raise AIProviderError("Gemini не ответил за отведённое время.", code="timeout", retryable=True) from exc
        except Exception as exc:
            code = self._classify_error(exc)
            raise AIProviderError(self._friendly_error(code), code=code, retryable=code in {"rate_limited", "network"}) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        text = (getattr(response, "text", None) or "").strip()
        if not text:
            raise AIProviderError("Gemini вернул пустой ответ.", code="empty_response", retryable=True)

        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", None) if usage else None
        completion_tokens = getattr(usage, "candidates_token_count", None) if usage else None
        total_tokens = getattr(usage, "total_token_count", None) if usage else None

        return AIResponse(
            text=text,
            provider=self.name,
            model=self.model,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    def _build_prompt(self, messages: list[AIMessage]) -> str:
        lines = []
        for message in messages:
            role = "Пользователь" if message.role == "user" else "Ассистент"
            lines.append(f"{role}: {message.content}")
        return "\n\n".join(lines)

    def _classify_error(self, exc: Exception) -> str:
        text = str(exc).lower()
        if "api key" in text or "unauthenticated" in text or "permission" in text:
            return "auth"
        if "429" in text or "quota" in text or "rate" in text:
            return "rate_limited"
        if "timeout" in text or "deadline" in text:
            return "timeout"
        if "network" in text or "connection" in text or "unavailable" in text:
            return "network"
        return "provider_error"

    def _friendly_error(self, code: str) -> str:
        return {
            "auth": "Gemini API ключ неверный или не имеет доступа.",
            "rate_limited": "Gemini временно ограничил запросы или квоту.",
            "timeout": "Gemini не ответил за отведённое время.",
            "network": "Не удалось подключиться к Gemini API.",
        }.get(code, "Gemini API временно недоступен.")
