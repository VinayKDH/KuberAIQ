"""Google OAuth API tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_google_callback_disabled_in_mock_mode(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/google/callback",
        json={
            "code": "test-code",
            "code_verifier": "test-verifier",
            "redirect_uri": "http://localhost:3000/auth/callback",
        },
    )
    assert resp.status_code == 403
