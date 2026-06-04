import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security import create_access_token
from tests.fixtures.committed import seed_user

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def auth_user(committed_client: AsyncClient, pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    user_id = await seed_user(eng, "user", f"otp_{uuid.uuid4().hex[:6]}@example.com")
    await eng.dispose()
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


@pytest.mark.asyncio
async def test_send_and_verify_otp_flow(committed_client: AsyncClient, auth_user):
    send = await committed_client.post(
        "/api/v1/auth/phone/send-otp",
        json={"phone": "79161234567"},
        headers=auth_user,
    )
    assert send.status_code == 200, send.text
    code = send.json()["debug_otp"]

    verify = await committed_client.post(
        "/api/v1/auth/phone/verify-otp",
        json={"phone": "79161234567", "code": code},
        headers=auth_user,
    )
    assert verify.status_code == 200
    assert verify.json()["phone_verified"] is True


@pytest.mark.asyncio
async def test_wrong_code_returns_422(committed_client: AsyncClient, auth_user):
    await committed_client.post(
        "/api/v1/auth/phone/send-otp",
        json={"phone": "79161234999"},
        headers=auth_user,
    )
    bad = await committed_client.post(
        "/api/v1/auth/phone/verify-otp",
        json={"phone": "79161234999", "code": "000000"},
        headers=auth_user,
    )
    assert bad.status_code == 422


@pytest.mark.asyncio
async def test_invalid_phone_format_422(committed_client: AsyncClient, auth_user):
    resp = await committed_client.post(
        "/api/v1/auth/phone/send-otp",
        json={"phone": "12345"},
        headers=auth_user,
    )
    assert resp.status_code == 422
