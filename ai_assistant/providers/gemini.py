from __future__ import annotations

import asyncio
import time
import logging

from ..config import AIConfig
from .base import AIMessage, AIProviderError, AIResponse


class GeminiProvider:
    name = "gemini"

    def __init__(self, config: AIConfig):
        self.model = config.gemini_model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
        self.timeout = config.timeout
        self.api_keys = config.gemini_api_keys
        self.current_key_index = 0

        if not self.api_keys:
            raise AIProviderError("Gemini API ключи не указаны.", code="missing_api_key")

        try:
            from google import genai
            from google.genai import types
        except Exception as exc:
            raise AIProviderError("Не установлен официальный Gemini SDK `google-genai`.", code="missing_sdk") from exc

        self._types = types
        self.client = genai.Client(api_key=self.api_keys[self.current_key_index])

    def _rotate_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        from google import genai
        self.client = genai.Client(api_key=self.api_keys[self.current_key_index])
        logging.info("Gemini API key rotated to #%d", self.current_key_index + 1)

    async def generate(self, messages: list[AIMessage], system_prompt: str) -> AIResponse:
        # Using the structured format expected by Gemini SDK for chat
        contents = []
        for message in messages:
            role = "user" if message.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": message.content}]})
        
        # Ensure contents is not empty as Gemini API requires it
        if not contents:
            contents.append({"role": "user", "parts": [{"text": "Привет"}]})
        
        logging.info("[AI] Constructed messages list for Gemini: %s", contents)
        config = self._types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
        )

        last_error = None
        for attempt in range(len(self.api_keys)):
            started = time.perf_counter()
            logging.info("Gemini API call starting for model=%s (attempt %d)", self.model, attempt + 1)
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.models.generate_content,
                        model=self.model,
                        contents=contents,
                        config=config,
                    ),
                    timeout=self.timeout,
                )
                # Success
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

            except Exception as exc:
                last_error = exc
                logging.error("Gemini API error (attempt %d): %s", attempt + 1, exc)
                code = self._classify_error(exc)
                if code in {"rate_limited", "auth", "network"}:
                    self._rotate_key()
                    continue
                raise AIProviderError(self._friendly_error(code), code=code, retryable=False) from exc
        
        raise AIProviderError("Все Gemini ключи исчерпаны или недоступны.", code="all_providers_failed") from last_error

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
