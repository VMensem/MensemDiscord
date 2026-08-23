from __future__ import annotations

import logging

from .config import AIConfig, load_ai_config
from .database import add_message, check_rate_limit, cleanup_history, clear_history, get_config, get_history
from .providers import AIMessage, AIProviderError, AIResponse
from .client_pool import AIClientPool


class AIClient:
    def __init__(self, config: AIConfig | None = None):
        self.config = config or load_ai_config()
        self.pool: AIClientPool | None = None
        self.startup_error: AIProviderError | None = None

        if self.config.provider == "none":
            return

        try:
            self.pool = AIClientPool(self.config)
        except AIProviderError as exc:
            self.startup_error = exc
        except Exception as exc:
            self.startup_error = AIProviderError(str(exc), code="provider_init_failed")

    @property
    def provider_name(self) -> str:
        if self.pool is not None and self.pool.providers:
            return self.pool.providers[0].name
        return self.config.provider

    async def is_enabled(self, guild_id: int) -> bool:
        enabled = str(await get_config(guild_id, "enabled", "true") or "true").strip().lower()
        return self.config.provider != "none" and enabled not in {"0", "false", "no", "off"}

    @property
    def is_ready(self) -> bool:
        return self.pool is not None and self.startup_error is None and bool(self.pool.providers)

    async def get_limit_per_hour(self, guild_id: int) -> int:
        raw = await get_config(guild_id, "limit_per_hour", "20")
        try:
            return max(1, int(raw or 20))
        except (TypeError, ValueError):
            return 20

    async def rate_limit_ok(self, user_id: int, guild_id: int) -> bool:
        limit = await self.get_limit_per_hour(guild_id)
        return await check_rate_limit(user_id, limit)

    async def generate(self, user_id: int, guild_id: int, prompt: str) -> AIResponse:
        if not await self.is_enabled(guild_id):
            raise AIProviderError("AI-ассистент отключён.", code="disabled")
        if self.startup_error is not None:
            raise self.startup_error
        if self.pool is None:
            raise AIProviderError("AI-провайдер не настроен.", code="disabled")

        logging.info("[AI] Loading history")
        await cleanup_history(user_id, self.config.history_limit, self.config.history_ttl_days)
        await add_message(user_id, "user", prompt)
        history_rows = await get_history(user_id, limit=self.config.history_limit, ttl_days=self.config.history_ttl_days)
        messages = [AIMessage(role=row["role"], content=row["message"]) for row in history_rows]
        logging.info("[AI] History loaded: %d messages", len(messages))
        # Log the content of the history to debug if it's being populated
        for i, msg in enumerate(messages):
            logging.info(f"[AI] History msg {i}: {msg.role}: {msg.content[:50]}...")

        # Knowledge Base retrieval
        logging.info("[AI] Loading knowledge")
        from .knowledge_base import get_knowledge
        kb_entries = await get_knowledge(guild_id, query_text=prompt) # Simplified search
        logging.info("[AI] Knowledge loaded: %d entries", len(kb_entries))
        
        system_prompt = self.config.system_prompt
        if kb_entries:
            kb_text = "\n\n".join([f"### {e['title']}\n{e['content']}" for e in kb_entries])
            system_prompt += f"\n\nДополнительная контекстная информация (используй её если релевантно):\n{kb_text}"

        logging.info("[AI] Calling AI provider with system_prompt len: %d", len(system_prompt))
        response = await self.pool.generate(messages, system_prompt)
        logging.info("[AI] AI response received")
        
        await add_message(user_id, "assistant", response.text)
        await cleanup_history(user_id, self.config.history_limit, self.config.history_ttl_days)
        logging.info("[AI] History saved")

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

    async def clear_history(self, user_id: int) -> None:
        await clear_history(user_id)
