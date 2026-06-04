import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security import create_access_token
from tests.fixtures.committed import seed_user

pytestmark = pytest.mark.integration


async def _headers(pg_container, role: str = "user") -> dict[str, str]:
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    uid = await seed_user(eng, role, f"tk_{uuid.uuid4().hex[:6]}@example.com")
    await eng.dispose()
    return {"Authorization": f"Bearer {create_access_token(uid)}"}


@pytest.mark.asyncio
async def test_user_creates_and_views_own_ticket(
    committed_client: AsyncClient, pg_container
):
    owner = await _headers(pg_container)
    created = await committed_client.post(
        "/api/v1/tickets",
        json={"type": "support_inquiry", "title": "Help"},
        headers=owner,
    )
    assert created.status_code == 201, created.text
    tid = created.json()["id"]
    got = await committed_client.get(f"/api/v1/tickets/{tid}", headers=owner)
    assert got.status_code == 200
    assert got.json()["ticket"]["title"] == "Help"


@pytest.mark.asyncio
async def test_non_owner_non_staff_cannot_view(
    committed_client: AsyncClient, pg_container
):
    owner = await _headers(pg_container)
    other = await _headers(pg_container)
    tid = (
        await committed_client.post(
            "/api/v1/tickets",
            json={"type": "support_inquiry", "title": "Help"},
            headers=owner,
        )
    ).json()["id"]
    resp = await committed_client.get(f"/api/v1/tickets/{tid}", headers=other)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_staff_lists_and_patches(committed_client: AsyncClient, pg_container):
    owner = await _headers(pg_container)
    staff = await _headers(pg_container, role="support")
    tid = (
        await committed_client.post(
            "/api/v1/tickets",
            json={"type": "listing_report", "title": "Bad"},
            headers=owner,
        )
    ).json()["id"]
    listing = await committed_client.get("/api/v1/tickets", headers=staff)
    assert listing.status_code == 200
    assert any(t["id"] == tid for t in listing.json())
    patched = await committed_client.patch(
        f"/api/v1/tickets/{tid}", json={"status": "in_progress"}, headers=staff
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_moderator_cannot_access_tickets(
    committed_client: AsyncClient, pg_container
):
    moderator = await _headers(pg_container, role="moderator")
    resp = await committed_client.get("/api/v1/tickets", headers=moderator)
    assert resp.status_code == 403
