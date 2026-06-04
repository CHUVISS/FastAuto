import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security import create_access_token
from tests.fixtures.committed import seed_user

pytestmark = pytest.mark.integration


async def _engine(pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    return create_async_engine(url, connect_args={"statement_cache_size": 0})


async def _seed_listing(eng, seller_id) -> str:
    listing_id = str(uuid.uuid4())
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO catalog.modifications (id) VALUES ('M1') ON CONFLICT DO NOTHING"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO listings (id, seller_id, modification_id, mark_id, model_id, "
                "year, price, mileage, color_id, condition, city_id, status, "
                "license_plate_edit_count) VALUES "
                "(:id, :s, 'M1', 'BMW', 'BMW_5', 2019, 2500000, 1, 'black', 'good', "
                "'7700000000000', 'active', 0)"
            ),
            {"id": listing_id, "s": seller_id},
        )
    return listing_id


@pytest_asyncio.fixture
async def setup(committed_client: AsyncClient, pg_container):
    eng = await _engine(pg_container)
    seller_id = await seed_user(eng, "user", f"seller_{uuid.uuid4().hex[:6]}@e.com")
    user_id = await seed_user(eng, "user", f"u_{uuid.uuid4().hex[:6]}@e.com")
    listing_id = await _seed_listing(eng, seller_id)
    await eng.dispose()
    return {
        "listing_id": listing_id,
        "headers": {"Authorization": f"Bearer {create_access_token(user_id)}"},
        "seller_headers": {"Authorization": f"Bearer {create_access_token(seller_id)}"},
    }


@pytest.mark.asyncio
async def test_add_list_remove_favorite(committed_client, setup):
    h = setup["headers"]
    lid = setup["listing_id"]

    add = await committed_client.post(
        "/api/v1/favorites", json={"listing_id": lid}, headers=h
    )
    assert add.status_code == 200 and add.json()["added"] is True

    # duplicate add is idempotent
    dup = await committed_client.post(
        "/api/v1/favorites", json={"listing_id": lid}, headers=h
    )
    assert dup.json()["added"] is False

    listed = await committed_client.get("/api/v1/favorites", headers=h)
    assert lid in [row["id"] for row in listed.json()]

    rm = await committed_client.delete(f"/api/v1/favorites/{lid}", headers=h)
    assert rm.status_code == 200
    listed2 = await committed_client.get("/api/v1/favorites", headers=h)
    assert listed2.json() == []


@pytest.mark.asyncio
async def test_owner_sees_favorite_count(committed_client, setup):
    lid = setup["listing_id"]
    await committed_client.post(
        "/api/v1/favorites", json={"listing_id": lid}, headers=setup["headers"]
    )
    owner_view = await committed_client.get(
        f"/api/v1/listings/{lid}", headers=setup["seller_headers"]
    )
    assert owner_view.json()["favorites_count"] == 1

    anon_view = await committed_client.get(f"/api/v1/listings/{lid}")
    assert "favorites_count" not in anon_view.json()
