from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

_BASE = "/api/v1/admin"
_STATS_URL = f"{_BASE}/stats"
_USERS_URL = f"{_BASE}/users"


async def test_stats_requires_admin(
    committed_client: AsyncClient, manager_headers: dict
):
    resp = await committed_client.get(_STATS_URL, headers=manager_headers)
    assert resp.status_code == 403


async def test_stats_requires_auth(committed_client: AsyncClient):
    resp = await committed_client.get(_STATS_URL)
    assert resp.status_code == 401


async def test_stats_returns_dashboard(
    committed_client: AsyncClient,
    admin_headers: dict,
    pg_container,
    engine,
    monkeypatch,  # noqa: ARG001
):
    from contextlib import asynccontextmanager

    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    from app.services.admin import admin_service

    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    test_eng = create_async_engine(url, connect_args={"statement_cache_size": 0})

    @asynccontextmanager
    async def _test_session_factory():
        async with test_eng.connect() as conn:
            async with AsyncSession(bind=conn, expire_on_commit=False) as s:
                yield s

    monkeypatch.setattr(admin_service, "async_session_factory", _test_session_factory)

    resp = await committed_client.get(_STATS_URL, headers=admin_headers)
    await test_eng.dispose()
    assert resp.status_code == 200
    body = resp.json()
    assert "total_listings" in body
    assert "active_listings" in body
    assert "total_reservations" in body
    assert "active_reservations" in body
    assert "settling_reservations" in body
    assert "completed_reservations" in body
    assert "total_users" in body
    assert "open_tickets" in body


async def test_list_admin_users_requires_admin(
    committed_client: AsyncClient, manager_headers: dict
):
    resp = await committed_client.get(_USERS_URL, headers=manager_headers)
    assert resp.status_code == 403


async def test_list_admin_users_returns_list(
    committed_client: AsyncClient, admin_headers: dict
):
    resp = await committed_client.get(_USERS_URL, headers=admin_headers)
    assert resp.status_code == 200
    assert "data" in resp.json()


async def test_create_admin_user_returns_201(
    committed_client: AsyncClient, admin_headers: dict
):
    resp = await committed_client.post(
        _USERS_URL,
        json={
            "email": "newmanager@example.org",
            "password": "Pass123!",
            "full_name": "New Manager",
            "role": "manager",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "manager"


async def test_create_admin_user_duplicate_email_returns_400(
    committed_client: AsyncClient, admin_headers: dict
):
    body = {
        "email": "dup@example.org",
        "password": "Pass123!",
        "full_name": "Dup",
        "role": "support",
    }
    await committed_client.post(_USERS_URL, json=body, headers=admin_headers)
    resp = await committed_client.post(_USERS_URL, json=body, headers=admin_headers)
    assert resp.status_code == 400
