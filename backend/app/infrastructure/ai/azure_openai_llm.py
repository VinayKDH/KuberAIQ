"""Azure OpenAI adapter for intent routing and entity extraction."""
from __future__ import annotations

import json
from typing import Any

import httpx
import structlog

from app.core.config import settings
from app.core.constants import (
    AI_MAX_TOKENS_CLASSIFY,
    AI_MAX_TOKENS_EXTRACT,
    AI_MAX_TOKENS_GENERATE,
    AiRoute,
)
from app.infrastructure.ai.mock_llm import MockLlm
from app.infrastructure.ai.prompts.system import (
    CUSTOMER_AGENT_PROMPT,
    INVOICE_AGENT_PROMPT,
    ROUTER_SYSTEM_PROMPT,
)

logger = structlog.get_logger(__name__)

_INTENT_PROMPTS = {
    AiRoute.INVOICE: INVOICE_AGENT_PROMPT,
    AiRoute.CUSTOMER: CUSTOMER_AGENT_PROMPT,
}


class AzureOpenAiLlm:
    """Calls Azure OpenAI chat completions; falls back to MockLlm when unavailable."""

    def __init__(self) -> None:
        self._fallback = MockLlm()

    def _configured(self) -> bool:
        return bool(settings.azure_openai_endpoint and settings.azure_openai_api_key)

    async def _chat(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        json_mode: bool = False,
    ) -> str:
        if not self._configured():
            return await self._fallback.generate_text(system, user)

        url = (
            f"{settings.azure_openai_endpoint.rstrip('/')}/openai/deployments/"
            f"{settings.azure_openai_deployment}/chat/completions"
            f"?api-version={settings.azure_openai_api_version}"
        )
        payload: dict[str, Any] = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "api-key": settings.azure_openai_api_key or "",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()

        content = body["choices"][0]["message"]["content"]
        logger.info(
            "azure_openai_completion",
            deployment=settings.azure_openai_deployment,
            tokens=body.get("usage", {}).get("total_tokens"),
        )
        return content

    async def classify_intent(self, message: str) -> dict[str, Any]:
        if not self._configured():
            return await self._fallback.classify_intent(message)
        try:
            raw = await self._chat(
                system=ROUTER_SYSTEM_PROMPT,
                user=message,
                max_tokens=AI_MAX_TOKENS_CLASSIFY,
                json_mode=True,
            )
            return json.loads(raw)
        except Exception as exc:
            logger.warning("azure_openai_classify_fallback", error=str(exc))
            return await self._fallback.classify_intent(message)

    async def extract_entities(self, message: str, intent: str) -> dict[str, Any]:
        if not self._configured():
            return await self._fallback.extract_entities(message, intent)
        prompt = _INTENT_PROMPTS.get(intent)
        if not prompt:
            return {}
        try:
            raw = await self._chat(
                system=prompt + '\nOutput ONLY JSON with extracted fields.',
                user=message,
                max_tokens=AI_MAX_TOKENS_EXTRACT,
                json_mode=True,
            )
            return json.loads(raw)
        except Exception as exc:
            logger.warning("azure_openai_extract_fallback", error=str(exc))
            return await self._fallback.extract_entities(message, intent)

    async def generate_text(self, system: str, user: str) -> str:
        if not self._configured():
            return await self._fallback.generate_text(system, user)
        try:
            return await self._chat(
                system=system,
                user=user,
                max_tokens=AI_MAX_TOKENS_GENERATE,
            )
        except Exception as exc:
            logger.warning("azure_openai_generate_fallback", error=str(exc))
            return await self._fallback.generate_text(system, user)
