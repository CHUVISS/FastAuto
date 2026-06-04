from __future__ import annotations

import asyncio

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

_AUTH_BASE = "/api/v1/auth"
_ME_URL = f"{_AUTH_BASE}/me"


async def test_no_token_returns_401(committed_client: AsyncClient):
    resp = await committed_client.get(_ME_URL)
    assert resp.status_code == 401


async def test_malformed_token_returns_401(committed_client: AsyncClient):
    resp = await committed_client.get(
        _ME_URL, headers={"Authorization": "Bearer notavalidtoken"}
    )
    assert resp.status_code == 401


async def test_wrong_scheme_returns_401(committed_client: AsyncClient):
    resp = await committed_client.get(
        _ME_URL, headers={"Authorization": "Basic dXNlcjpwYXNz"}
    )
    assert resp.status_code == 401


async def test_empty_bearer_returns_401(committed_client: AsyncClient):
    resp = await committed_client.get(_ME_URL, headers={"Authorization": "Bearer "})
    assert resp.status_code == 401


async def test_admin_can_access_admin_endpoints(
    committed_client: AsyncClient, admin_headers: dict
):
    resp = await committed_client.get("/api/v1/admin/users", headers=admin_headers)
    assert resp.status_code == 200


async def test_manager_cannot_access_admin_users(
    committed_client: AsyncClient, manager_headers: dict
):
    resp = await committed_client.get("/api/v1/admin/users", headers=manager_headers)
    assert resp.status_code == 403


async def test_token_blacklisted_after_logout(committed_client: AsyncClient):
    await committed_client.post(
        f"{_AUTH_BASE}/register",
        json={
            "email": "logout_sec@example.org",
            "password": "TestPass123!",
            "full_name": "Logout Test",
        },
    )
    tokens = (
        await committed_client.post(
            f"{_AUTH_BASE}/login",
            json={
                "email": "logout_sec@example.org",
                "password": "TestPass123!",
            },
        )
    ).json()
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]
    headers = {"Authorization": f"Bearer {access}"}

    assert (await committed_client.get(_ME_URL, headers=headers)).status_code == 200

    await committed_client.post(
        f"{_AUTH_BASE}/logout",
        json={"refresh_token": refresh},
        headers=headers,
    )

    assert (await committed_client.get(_ME_URL, headers=headers)).status_code == 401


async def test_old_token_invalid_after_password_change(committed_client: AsyncClient):
    await committed_client.post(
        f"{_AUTH_BASE}/register",
        json={
            "email": "pwchange@example.org",
            "password": "OldPass123!",
            "full_name": "PW Change",
        },
    )
    tokens = (
        await committed_client.post(
            f"{_AUTH_BASE}/login",
            json={
                "email": "pwchange@example.org",
                "password": "OldPass123!",
            },
        )
    ).json()
    old_access = tokens["access_token"]
    headers = {"Authorization": f"Bearer {old_access}"}

    await asyncio.sleep(1)

    await committed_client.patch(
        f"{_AUTH_BASE}/me/password",
        json={"current_password": "OldPass123!", "new_password": "NewPass999!"},
        headers=headers,
    )

    resp = await committed_client.get(_ME_URL, headers=headers)
    assert resp.status_code == 401
