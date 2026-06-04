from __future__ import annotations

from contextlib import asynccontextmanager

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.admin import admin_service
from tests.short_tests._helpers import engine, seed_role

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_admin_dashboard_returns_reservation_aggregates(
    committed_client: AsyncClient, pg_container, monkeypatch
):
    _, admin_headers = await seed_role(pg_container, role="admin")
    test_eng = engine(pg_container)

    @asynccontextmanager
    async def _factory():
        async with (
            test_eng.connect() as conn,
            AsyncSession(bind=conn, expire_on_commit=False) as s,
        ):
            yield s

    monkeypatch.setattr(admin_service, "async_session_factory", _factory)

    response = await committed_client.get("/api/v1/admin/stats", headers=admin_headers)
    await test_eng.dispose()

    assert response.status_code == 200
    body = response.json()
    assert {
        "total_listings",
        "active_listings",
        "total_reservations",
        "active_reservations",
        "settling_reservations",
        "completed_reservations",
        "open_tickets",
    } <= body.keys()
