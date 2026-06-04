from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

_AUTH_BASE = "/api/v1/auth"


async def test_login_rate_limit_per_email(committed_client: AsyncClient):
    email = "ratelimit@example.org"
    await committed_client.post(
        f"{_AUTH_BASE}/register",
        json={
            "email": email,
            "password": "TestPass123!",
            "full_name": "Rate Limit Test",
        },
    )

    for _ in range(5):
        await committed_client.post(
            f"{_AUTH_BASE}/login",
            json={"email": email, "password": "WrongPass!!!"},
        )

    resp = await committed_client.post(
        f"{_AUTH_BASE}/login",
        json={"email": email, "password": "WrongPass!!!"},
    )
    assert resp.status_code == 429
