"""Regression tests for two runtime 500s seen from the frontend:

1. POST /favorites with a non-existent listing must return 404 (not a 500
   FK violation).
2. PATCH /user/profile must succeed even when the current user was resolved
   from the Redis auth cache (detached instance) — previously a 500
   users_pkey INSERT conflict.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from tests.fixtures.committed import seed_user
from tests.short_tests._helpers import auth_headers

pytestmark = pytest.mark.integration


async def _engine(pg_container):
    from sqlalchemy.ext.asyncio import create_async_engine

    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    return create_async_engine(url, connect_args={"statement_cache_size": 0})


@pytest.mark.asyncio
async def test_favorite_nonexistent_listing_returns_404(
    committed_client: AsyncClient, pg_container
):
    eng = await _engine(pg_container)
    user_id = await seed_user(eng, "user", f"u_{uuid.uuid4().hex[:6]}@e.com")
    await eng.dispose()

    response = await committed_client.post(
        "/api/v1/favorites",
        json={"listing_id": str(uuid.uuid4())},
        headers=auth_headers(user_id),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_profile_twice_succeeds_with_cached_user(
    committed_client: AsyncClient, pg_container
):
    eng = await _engine(pg_container)
    user_id = await seed_user(eng, "user", f"u_{uuid.uuid4().hex[:6]}@e.com")
    await eng.dispose()
    headers = {"Authorization": f"Bearer {create_access_token(user_id)}"}

    # First authed call populates the Redis auth cache, so the second request
    # resolves the user from cache (detached instance).
    first = await committed_client.patch(
        "/api/v1/user/profile", json={"full_name": "Иван Иванов"}, headers=headers
    )
    assert first.status_code == 200, first.text

    second = await committed_client.patch(
        "/api/v1/user/profile",
        json={"full_name": "Пётр Петров", "phone": "+7 (999) 123-45-67"},
        headers=headers,
    )
    assert second.status_code == 200, second.text
    assert second.json()["full_name"] == "Пётр Петров"
