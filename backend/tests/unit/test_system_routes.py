from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.routes.system import router

pytestmark = pytest.mark.unit


@pytest.fixture
def app() -> FastAPI:
    a = FastAPI()
    a.include_router(router)
    return a


@pytest.mark.asyncio
async def test_health_returns_ok(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "environment" in body


@pytest.mark.asyncio
async def test_health_not_in_openapi(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/openapi.json")
    paths = resp.json().get("paths", {})
    assert "/health" not in paths
