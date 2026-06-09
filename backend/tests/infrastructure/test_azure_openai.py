"""Azure OpenAI adapter tests."""
from __future__ import annotations

import pytest

from app.core.constants import AiRoute
from app.infrastructure.ai.azure_openai_llm import AzureOpenAiLlm


@pytest.mark.asyncio
async def test_azure_openai_falls_back_without_config() -> None:
    llm = AzureOpenAiLlm()
    result = await llm.classify_intent("Show unpaid invoices")
    assert result["route"] == AiRoute.COLLECTIONS


@pytest.mark.asyncio
async def test_azure_openai_uses_api_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "azure_openai_endpoint", "https://example.openai.azure.com")
    monkeypatch.setattr(config_mod.settings, "azure_openai_api_key", "test-key")
    monkeypatch.setattr(config_mod.settings, "azure_openai_deployment", "gpt-test")

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [{"message": {"content": '{"route":"dashboard","confidence":0.9}'}}],
                "usage": {"total_tokens": 42},
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, json, headers):
            return FakeResponse()

    monkeypatch.setattr(
        "app.infrastructure.ai.azure_openai_llm.httpx.AsyncClient",
        lambda **kwargs: FakeClient(),
    )

    llm = AzureOpenAiLlm()
    result = await llm.classify_intent("What is my revenue?")
    assert result["route"] == "dashboard"
