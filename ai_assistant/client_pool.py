from __future__ import annotations

import logging
from typing import Type

from .config import AIConfig
from .providers.base import AIMessage, AIProviderError, AIResponse
from .providers.gemini import GeminiProvider
from .providers.openai import OpenAIProvider


PROVIDER_FACTORIES: dict[str, Type[GeminiProvider | OpenAIProvider]] = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
}


class AIClientPool:
    def __init__(self, config: AIConfig):
        self.config = config
        self.providers: list[GeminiProvider | OpenAIProvider] = []
        self.current_index = 0
        self._initialize_providers()

    def _initialize_providers(self):
        factory = PROVIDER_FACTORIES.get(self.config.provider)
        if not factory:
            return

        keys = self.config.gemini_api_keys if self.config.provider == "gemini" else self.config.openai_api_keys
        
        for key in keys:
            try:
                # Patch the key in the provider itself without re-instantiating AIConfig
                provider = factory(self.config)
                if self.config.provider == "gemini":
                    provider.client.api_key = key
                else:
                    provider.client.api_key = key
                self.providers.append(provider)
            except Exception as e:
                logging.error(f"Failed to initialize provider {self.config.provider}: {e}")

    def get_provider(self) -> GeminiProvider | OpenAIProvider:
        if not self.providers:
            raise AIProviderError("Нет доступных AI-провайдеров.", code="no_providers")
        
        provider = self.providers[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.providers)
        return provider

    async def generate(self, messages: list[AIMessage], system_prompt: str) -> AIResponse:
        attempts = 0
        max_attempts = len(self.providers)
        
        while attempts < max_attempts:
            provider = self.get_provider()
            try:
                return await provider.generate(messages, system_prompt)
            except AIProviderError as e:
                if e.retryable and attempts < max_attempts - 1:
                    attempts += 1
                    logging.warning(f"AI provider {provider.name} failed, retrying. Attempt {attempts}/{max_attempts}")
                    continue
                raise e
        
        raise AIProviderError("Все AI-провайдеры вернули ошибку.", code="all_providers_failed")
