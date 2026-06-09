"""Mock LLM tests."""
from __future__ import annotations

import pytest

from app.core.constants import AiRoute
from app.infrastructure.ai.mock_llm import MockLlm


@pytest.mark.asyncio
async def test_mock_llm_classifies_dashboard_intent() -> None:
    llm = MockLlm()
    result = await llm.classify_intent("Show me revenue this month")
    assert result["route"] == AiRoute.DASHBOARD
    assert result["confidence"] >= 0.8


@pytest.mark.asyncio
async def test_mock_llm_generate_text() -> None:
    llm = MockLlm()
    text = await llm.generate_text("system", "hello")
    assert "Mock response" in text


@pytest.mark.asyncio
async def test_mock_llm_extracts_invoice_entities() -> None:
    llm = MockLlm()
    entities = await llm.extract_entities(
        "Create invoice ABC Traders for 50 bags at 350",
        AiRoute.INVOICE,
    )
    assert entities["quantity"] == 50
    assert entities["unit_price"] == 350.0


@pytest.mark.asyncio
async def test_mock_llm_extracts_customer_entities() -> None:
    llm = MockLlm()
    entities = await llm.extract_entities(
        "Add customer Raj Traders 9876543210",
        AiRoute.CUSTOMER,
    )
    assert entities["name"] == "Raj Traders"
    assert entities["phone"] == "9876543210"
