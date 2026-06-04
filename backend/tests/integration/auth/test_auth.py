from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

_BASE = "/api/v1/auth"
_REGISTER_URL = f"{_BASE}/register"
_LOGIN_URL = f"{_BASE}/login"
_REFRESH_URL = f"{_BASE}/refresh"
_LOGOUT_URL = f"{_BASE}/logout"
_ME_URL = f"{_BASE}/me"
_PWD_URL = f"{_BASE}/me/password"

_DEFAULT_EMAIL = "auth_test@example.org"
_DEFAULT_PWD = "TestPass123!"
_DEFAULT_NAME = "Auth Tester"


async def _register(client, email=_DEFAULT_EMAIL):
    resp = await client.post(
        _REGISTER_URL,
        json={
            "email": email,
            "password": _DEFAULT_PWD,
            "full_name": _DEFAULT_NAME,
        },
    )
    return resp


async def _login(client, email=_DEFAULT_EMAIL, password=_DEFAULT_PWD):
    resp = await client.post(_LOGIN_URL, json={"email": email, "password": password})
    return resp


async def test_register_returns_201_with_user(committed_client):
    resp = await _register(committed_client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == _DEFAULT_EMAIL
    assert body["full_name"] == _DEFAULT_NAME
    assert "id" in body
    assert "hashed_password" not in body


async def test_register_duplicate_email_returns_400(committed_client):
    await _register(committed_client)
    resp = await _register(committed_client)
    assert resp.status_code == 400


async def test_register_invalid_email_returns_422(committed_client):
    resp = await committed_client.post(
        _REGISTER_URL,
        json={
            "email": "not-an-email",
            "password": _DEFAULT_PWD,
            "full_name": _DEFAULT_NAME,
        },
    )
    assert resp.status_code == 422


async def test_login_returns_tokens(committed_client):
    await _register(committed_client)
    resp = await _login(committed_client)
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password_returns_401(committed_client):
    await _register(committed_client)
    resp = await _login(committed_client, password="WrongPass999!")
    assert resp.status_code == 401


async def test_login_unknown_email_returns_401(committed_client):
    resp = await _login(committed_client, email="nobody@example.org")
    assert resp.status_code == 401


async def test_me_returns_current_user(committed_client):
    await _register(committed_client)
    login_resp = await _login(committed_client)
    token = login_resp.json()["access_token"]

    resp = await committed_client.get(
        _ME_URL, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == _DEFAULT_EMAIL


async def test_me_without_token_returns_401(committed_client):
    resp = await committed_client.get(_ME_URL)
    assert resp.status_code == 401


async def test_me_with_bad_token_returns_401(committed_client):
    resp = await committed_client.get(
        _ME_URL, headers={"Authorization": "Bearer not.a.token"}
    )
    assert resp.status_code == 401


async def test_refresh_returns_new_tokens(committed_client):
    await _register(committed_client)
    login_resp = await _login(committed_client)
    refresh_token = login_resp.json()["refresh_token"]

    resp = await committed_client.post(
        _REFRESH_URL, json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_refresh_token_can_only_be_used_once(committed_client):
    await _register(committed_client)
    login_resp = await _login(committed_client)
    refresh_token = login_resp.json()["refresh_token"]

    await committed_client.post(_REFRESH_URL, json={"refresh_token": refresh_token})
    resp = await committed_client.post(
        _REFRESH_URL, json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 401


async def test_refresh_with_invalid_token_returns_401(committed_client):
    resp = await committed_client.post(_REFRESH_URL, json={"refresh_token": "invalid"})
    assert resp.status_code == 401


async def test_logout_returns_200(committed_client):
    await _register(committed_client)
    login_resp = await _login(committed_client)
    access = login_resp.json()["access_token"]
    refresh = login_resp.json()["refresh_token"]

    resp = await committed_client.post(
        _LOGOUT_URL,
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 200


async def test_after_logout_access_token_is_revoked(committed_client):
    await _register(committed_client)
    login_resp = await _login(committed_client)
    access = login_resp.json()["access_token"]
    refresh = login_resp.json()["refresh_token"]

    await committed_client.post(
        _LOGOUT_URL,
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer {access}"},
    )

    resp = await committed_client.get(
        _ME_URL, headers={"Authorization": f"Bearer {access}"}
    )
    assert resp.status_code == 401


async def test_change_password_success(committed_client):
    await _register(committed_client)
    login_resp = await _login(committed_client)
    access = login_resp.json()["access_token"]

    resp = await committed_client.patch(
        _PWD_URL,
        json={"current_password": _DEFAULT_PWD, "new_password": "NewPass999!"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 200


async def test_change_password_wrong_current_returns_400(committed_client):
    await _register(committed_client)
    login_resp = await _login(committed_client)
    access = login_resp.json()["access_token"]

    resp = await committed_client.patch(
        _PWD_URL,
        json={"current_password": "WrongOld111!", "new_password": "NewPass999!"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 400


async def test_change_password_requires_auth(committed_client):
    resp = await committed_client.patch(
        _PWD_URL,
        json={"current_password": _DEFAULT_PWD, "new_password": "NewPass999!"},
    )
    assert resp.status_code == 401
