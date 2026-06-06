"""LangGraph copilot build tests."""
from __future__ import annotations

import pytest

from app.infrastructure.ai.graph.build import CopilotGraph


@pytest.mark.asyncio
async def test_copilot_graph_handles_dashboard_query() -> None:
    graph = CopilotGraph()
    result = await graph.run(
        company_id="00000000-0000-4000-8000-000000000001",
        user_id="00000000-0000-4000-8000-000000000002",
        message="How much money is pending?",
        channel="web",
    )
    assert result["intent"]
    assert result["message"]
