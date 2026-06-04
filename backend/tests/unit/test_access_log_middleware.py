from __future__ import annotations

import pytest
import structlog.testing
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.middleware.access_log import AccessLogMiddleware
from app.api.middleware.request_id import RequestIdMiddleware

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _fresh_access_log_logger(monkeypatch):
    """Rebind the middleware's module-level logger to a fresh, unbound proxy.

    ``configure_logging`` runs with ``cache_logger_on_first_use=True``; once an
    earlier test exercises the access-log middleware, its bound logger is cached
    against the production processor chain and ``capture_logs`` (which swaps the
    active processor list in place) can no longer intercept it. Rebinding to a
    fresh lazy proxy per test makes capture work regardless of test order.
    """
    from app.api.middleware import access_log

    monkeypatch.setattr(access_log, "log", structlog.get_logger("access_log_test"))


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(RequestIdMiddleware)

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


@pytest.fixture
def app():
    return _make_app()


@pytest.mark.asyncio
async def test_access_log_emitted_for_normal_request(app):
    with structlog.testing.capture_logs() as logs:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/ping")

    assert resp.status_code == 200
    assert len(logs) == 1
    entry = logs[0]
    assert entry["event"] == "request"
    assert entry["method"] == "GET"
    assert entry["path"] == "/ping"
    assert entry["status"] == 200
    assert "duration_ms" in entry


@pytest.mark.asyncio
async def test_health_path_not_logged(app):
    with structlog.testing.capture_logs() as logs:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.get("/health")

    assert logs == []


@pytest.mark.asyncio
async def test_access_log_includes_request_id(app):
    with structlog.testing.capture_logs() as logs:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.get("/ping", headers={"X-Request-ID": "test-id-123"})

    entry = logs[0]
    assert entry.get("request_id") == "test-id-123"


@pytest.mark.asyncio
async def test_access_log_5xx_status(app):
    from fastapi import HTTPException

    @app.get("/boom")
    async def boom():
        raise HTTPException(status_code=500, detail="err")

    with structlog.testing.capture_logs() as logs:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.get("/boom")

    assert logs[0]["status"] == 500
