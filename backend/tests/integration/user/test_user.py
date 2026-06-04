from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

_AUTH_BASE = "/api/v1/auth"
_USER_BASE = "/api/v1/user"

_DEFAULT_EMAIL = "usertest@example.org"
_DEFAULT_PWD = "TestPass123!"


async def _register_and_login(client: AsyncClient, email: str = _DEFAULT_EMAIL):
    await client.post(
        f"{_AUTH_BASE}/register",
        json={
            "email": email,
            "password": _DEFAULT_PWD,
            "full_name": "User Tester",
        },
    )
    resp = await client.post(
        f"{_AUTH_BASE}/login", json={"email": email, "password": _DEFAULT_PWD}
    )
    return resp.json()


async def _user_headers(client: AsyncClient, email: str = _DEFAULT_EMAIL):
    tokens = await _register_and_login(client, email)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_get_profile_returns_user(committed_client: AsyncClient):
    headers = await _user_headers(committed_client)
    resp = await committed_client.get(f"{_USER_BASE}/profile", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == _DEFAULT_EMAIL


async def test_get_profile_requires_auth(committed_client: AsyncClient):
    resp = await committed_client.get(f"{_USER_BASE}/profile")
    assert resp.status_code == 401


async def test_update_profile_name(committed_client: AsyncClient):
    headers = await _user_headers(committed_client)
    resp = await committed_client.patch(
        f"{_USER_BASE}/profile", json={"full_name": "New Name"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "New Name"


async def test_update_profile_phone(committed_client: AsyncClient):
    headers = await _user_headers(committed_client)
    resp = await committed_client.patch(
        f"{_USER_BASE}/profile", json={"phone": "79001112244"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["phone"] == "79001112244"


async def test_update_profile_phone_conflict_returns_409(committed_client: AsyncClient):
    h1 = await _user_headers(committed_client, "user1@example.org")
    await committed_client.patch(
        f"{_USER_BASE}/profile", json={"phone": "79001119999"}, headers=h1
    )
    h2 = await _user_headers(committed_client, "user2@example.org")
    resp = await committed_client.patch(
        f"{_USER_BASE}/profile", json={"phone": "79001119999"}, headers=h2
    )
    assert resp.status_code == 409
