"""Smoke test -- proves the test harness itself works."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
