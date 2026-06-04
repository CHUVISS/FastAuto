import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security import create_access_token
from tests.fixtures.committed import seed_user

pytestmark = pytest.mark.integration


async def _seed(pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    seller = await seed_user(eng, "user", f"sell_{uuid.uuid4().hex[:6]}@example.com")
    moderator = await seed_user(
        eng, "moderator", f"mod_{uuid.uuid4().hex[:6]}@example.com"
    )
    listing_id = uuid.uuid4()
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO catalog.modifications (id) VALUES ('M1') "
                "ON CONFLICT DO NOTHING"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO listings (id, seller_id, modification_id, mark_id, "
                "model_id, year, price, mileage, color_id, condition, city_id, "
                "status, license_plate_edit_count, viewing_enabled) VALUES "
                "(:id, :s, 'M1', 'BMW', 'BMW_5', 2019, 2500000, 1, 'black', 'good', '7700000000000', "
                "'pending_review', 0, false)"
            ),
            {"id": listing_id, "s": seller},
        )
    await eng.dispose()
    return {
        "listing_id": str(listing_id),
        "mod": {"Authorization": f"Bearer {create_access_token(moderator)}"},
    }


@pytest_asyncio.fixture
async def pending(committed_client: AsyncClient, pg_container):
    return await _seed(pg_container)


@pytest.mark.asyncio
async def test_moderation_queue_and_approve(committed_client: AsyncClient, pending):
    queue = await committed_client.get(
        "/api/v1/admin/listings?status=pending_review", headers=pending["mod"]
    )
    assert queue.status_code == 200, queue.text
    assert any(pending["listing_id"] == x["id"] for x in queue.json())

    approved = await committed_client.post(
        f"/api/v1/admin/listings/{pending['listing_id']}/approve",
        headers=pending["mod"],
    )
    assert approved.status_code == 200, approved.text
    body = approved.json()
    assert body["status"] == "active"
    assert body["published_at"] is not None
    assert body["expires_at"] is not None


@pytest.mark.asyncio
async def test_reject_archives_with_reason(committed_client: AsyncClient, pending):
    rej = await committed_client.post(
        f"/api/v1/admin/listings/{pending['listing_id']}/reject",
        json={"reason": "Bad photos"},
        headers=pending["mod"],
    )
    assert rej.status_code == 200, rej.text
    assert rej.json()["status"] == "archived"


@pytest.mark.asyncio
async def test_queue_requires_moderator(committed_client: AsyncClient, pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    support = await seed_user(eng, "support", f"sup_{uuid.uuid4().hex[:6]}@example.com")
    await eng.dispose()
    resp = await committed_client.get(
        "/api/v1/admin/listings?status=pending_review",
        headers={"Authorization": f"Bearer {create_access_token(support)}"},
    )
    assert resp.status_code == 403
