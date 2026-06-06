"""LangGraph router tests."""
from __future__ import annotations

import pytest

from app.core.constants import AiRoute
from app.infrastructure.ai.graph.router import route_message


@pytest.mark.asyncio
async def test_router_invoice_intent():
    result = await route_message({"message": "Invoice ABC Traders for 50 bags cement at 350"})
    assert result["route"] == AiRoute.INVOICE


@pytest.mark.asyncio
async def test_router_collections_intent():
    result = await route_message({"message": "Show me all overdue invoices"})
    assert result["route"] == AiRoute.COLLECTIONS


@pytest.mark.asyncio
async def test_router_dashboard_intent():
    result = await route_message({"message": "What is my revenue this month?"})
    assert result["route"] == AiRoute.DASHBOARD


@pytest.mark.asyncio
async def test_router_clarify_intent():
    result = await route_message({"message": "hello there"})
    assert result["route"] == AiRoute.CLARIFY
