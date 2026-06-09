"""Tests for overdue background job."""
from __future__ import annotations

import pytest

from app.workers.jobs import mark_overdue_all_companies


@pytest.mark.asyncio
async def test_mark_overdue_all_companies_runs() -> None:
    await mark_overdue_all_companies()
