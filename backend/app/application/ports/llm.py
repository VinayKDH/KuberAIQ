"""LLM port — abstract interface for language model providers."""
from __future__ import annotations

from typing import Any, Protocol


class LlmPort(Protocol):
    async def classify_intent(self, message: str) -> dict[str, Any]: ...

    async def extract_entities(self, message: str, intent: str) -> dict[str, Any]: ...

    async def generate_text(self, system: str, user: str) -> str: ...
