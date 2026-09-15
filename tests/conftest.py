"""
Shared pytest fixtures.

We use anyio rather than pytest-asyncio: FastAPI already depends on anyio,
and anyio ships its own pytest plugin, so this needs no extra dependency.
The anyio_backend fixture pins tests to asyncio -- without it anyio runs
every async test twice, once on asyncio and once on trio.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """An HTTP client that talks to the app in-process -- no server, no TCP."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
