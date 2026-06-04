from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.short_tests._helpers import auth_headers, seed_role

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_login_then_get_profile_returns_ok(
    committed_client: AsyncClient, pg_container
):
    user_id, headers = await seed_role(pg_container, role="user")

    response = await committed_client.get("/api/v1/user/profile", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == user_id


@pytest.mark.asyncio
async def test_get_profile_without_token_returns_unauthorized(
    committed_client: AsyncClient,
):
    response = await committed_client.get("/api/v1/user/profile")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_admin_users_as_regular_user_returns_forbidden(
    committed_client: AsyncClient, pg_container
):
    user_id, _ = await seed_role(pg_container, role="user")

    response = await committed_client.get(
        "/api/v1/admin/users", headers=auth_headers(user_id)
    )

    assert response.status_code == 403
