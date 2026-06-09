"""Collections agent tests."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.constants import AiIntent
from app.infrastructure.ai.graph.agents.collections_agent import run_collections_agent


@pytest.mark.asyncio
async def test_collections_agent_bulk_reminder_requires_confirmation() -> None:
    collection = MagicMock()
    collection.list_overdue = AsyncMock(return_value=[])
    collection.bulk_preview = AsyncMock(
        return_value={"count": 2, "total_outstanding": 5000, "invoices": []}
    )
    state = {
        "message": "send reminders to all overdue",
        "company_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "services": {"collection": collection},
        "confirmed": False,
    }
    result = await run_collections_agent(state)
    response = result["response"]
    assert response["requires_confirmation"] is True
    assert response["pending_action"]["type"] == AiIntent.BULK_SEND_REMINDERS
