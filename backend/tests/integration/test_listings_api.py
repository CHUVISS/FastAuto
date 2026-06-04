import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security import create_access_token
from tests.fixtures.committed import seed_user

pytestmark = pytest.mark.integration


async def _seed_catalog(eng):
    async with eng.begin() as conn:
        for stmt in [
            "INSERT INTO catalog.marks (id,name,popular) VALUES ('BMW','BMW',true) ON CONFLICT DO NOTHING",
            "INSERT INTO catalog.models (id,mark_id,name) VALUES ('BMW_5','BMW','5') ON CONFLICT DO NOTHING",
            "INSERT INTO catalog.generations (id,model_id,name,year_from,year_to) "
            "VALUES ('G1','BMW_5','VII',2016,2023) ON CONFLICT DO NOTHING",
            "INSERT INTO catalog.configurations (id,generation_id,body_type) "
            "VALUES ('C1','G1','SEDAN') ON CONFLICT DO NOTHING",
            "INSERT INTO catalog.modifications (id,mark_id,model_id,generation_id,configuration_id,name) "
            "VALUES ('M1','BMW','BMW_5','G1','C1','3.0 AT') ON CONFLICT DO NOTHING",
            "INSERT INTO catalog.specifications (id,engine_type) VALUES ('M1','Дизельный') ON CONFLICT DO NOTHING",
        ]:
            await conn.execute(text(stmt))


@pytest_asyncio.fixture
async def seller(committed_client: AsyncClient, pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    await _seed_catalog(eng)
    user_id = await seed_user(eng, "user", f"seller_{uuid.uuid4().hex[:6]}@example.com")
    await eng.dispose()
    headers = {"Authorization": f"Bearer {create_access_token(user_id)}"}
    return user_id, headers


def _payload(**over):
    base = {
        "modification_id": "M1",
        "year": 2019,
        "price": 2_500_000,
        "mileage": 85000,
        "color_id": "black",
        "condition": "good",
        "city_id": "7700000000000",
        "vin": "WBA12345678901234",
        "viewing_enabled": False,
    }
    base.update(over)
    return base


@pytest.mark.asyncio
async def test_create_draft_and_fetch(committed_client: AsyncClient, seller):
    _, headers = seller
    resp = await committed_client.post(
        "/api/v1/listings", json=_payload(), headers=headers
    )
    assert resp.status_code == 201, resp.text
    listing_id = resp.json()["id"]

    detail = await committed_client.get(f"/api/v1/listings/{listing_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["modification_id"] == "M1"
    assert body["mark_id"] == "BMW"
    assert body["status"] == "draft"


@pytest.mark.asyncio
async def test_create_rejects_year_outside_generation(
    committed_client: AsyncClient, seller
):
    _, headers = seller
    resp = await committed_client.post(
        "/api/v1/listings", json=_payload(year=2030), headers=headers
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_vin_edit_rejected(committed_client: AsyncClient, seller):
    _, headers = seller
    listing_id = (
        await committed_client.post(
            "/api/v1/listings", json=_payload(), headers=headers
        )
    ).json()["id"]
    resp = await committed_client.patch(
        f"/api/v1/listings/{listing_id}",
        json={"vin": "AAA12345678901234"},
        headers=headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_viewing_schedule_merge_no_duplicates(
    committed_client: AsyncClient, seller
):
    _, headers = seller
    listing_id = (
        await committed_client.post(
            "/api/v1/listings", json=_payload(), headers=headers
        )
    ).json()["id"]
    schedule = {
        "repeat_weekly": True,
        "template": [
            {"weekday": 0, "time_from": "10:00:00", "time_to": "12:00:00"},
            {"weekday": 2, "time_from": "10:00:00", "time_to": "12:00:00"},
        ],
    }
    r1 = await committed_client.put(
        f"/api/v1/listings/{listing_id}/viewing-schedule",
        json=schedule,
        headers=headers,
    )
    assert r1.status_code == 200, r1.text
    windows1 = await committed_client.get(
        f"/api/v1/listings/{listing_id}/viewing-windows"
    )
    count1 = len(windows1.json())
    assert count1 >= 1

    await committed_client.put(
        f"/api/v1/listings/{listing_id}/viewing-schedule",
        json=schedule,
        headers=headers,
    )
    windows2 = await committed_client.get(
        f"/api/v1/listings/{listing_id}/viewing-windows"
    )
    assert len(windows2.json()) == count1


@pytest.mark.asyncio
async def test_max_active_listings_returns_422(
    committed_client: AsyncClient, seller, pg_container
):
    user_id, headers = seller
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    async with eng.begin() as conn:
        for _ in range(5):
            await conn.execute(
                text(
                    "INSERT INTO listings (id, seller_id, modification_id, mark_id, model_id, "
                    "year, price, mileage, color_id, condition, city_id, status, "
                    "license_plate_edit_count) VALUES "
                    "(gen_random_uuid(), :s, 'M1', 'BMW', 'BMW_5', 2019, 2500000, 1, 'black', "
                    "'good', '7700000000000', 'active', 0)"
                ),
                {"s": user_id},
            )
    await eng.dispose()
    resp = await committed_client.post(
        "/api/v1/listings", json=_payload(), headers=headers
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_keyset_cursor_paginates_without_duplicates(
    committed_client: AsyncClient, seller, pg_container
):
    user_id, _ = seller
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    listing_ids: list[str] = []
    async with eng.begin() as conn:
        for i in range(7):
            lid = uuid.uuid4()
            listing_ids.append(str(lid))
            await conn.execute(
                text(
                    "INSERT INTO listings (id, seller_id, modification_id, mark_id, "
                    "model_id, year, price, mileage, color_id, condition, city_id, "
                    "status, license_plate_edit_count, viewing_enabled, "
                    "created_at, published_at) VALUES "
                    "(:id, :s, 'M1', 'BMW', 'BMW_5', 2019, :p, 1, 'black', 'good', "
                    "'7700000000000', 'active', 0, false, "
                    "now() - (:i || ' minutes')::interval, "
                    "now() - (:i || ' minutes')::interval)"
                ),
                {"id": lid, "s": user_id, "p": 1_000_000 + i, "i": str(i)},
            )
    await eng.dispose()

    page1 = await committed_client.get(
        "/api/v1/listings", params={"sort": "newest", "limit": 3}
    )
    body1 = page1.json()
    assert len(body1["items"]) == 3
    assert body1["next_cursor"] is not None
    ids1 = [r["id"] for r in body1["items"]]

    page2 = await committed_client.get(
        "/api/v1/listings",
        params={"sort": "newest", "limit": 3, "cursor": body1["next_cursor"]},
    )
    body2 = page2.json()
    assert len(body2["items"]) == 3
    assert body2["next_cursor"] is not None
    ids2 = [r["id"] for r in body2["items"]]

    page3 = await committed_client.get(
        "/api/v1/listings",
        params={"sort": "newest", "limit": 3, "cursor": body2["next_cursor"]},
    )
    body3 = page3.json()
    ids3 = [r["id"] for r in body3["items"]]
    assert len(ids3) == 1
    assert body3["next_cursor"] is None

    seen = set(ids1) | set(ids2) | set(ids3)
    assert len(seen) == len(ids1) + len(ids2) + len(ids3) == 7


@pytest.mark.asyncio
async def test_keyset_cursor_price_asc_sort(
    committed_client: AsyncClient, seller, pg_container
):
    user_id, _ = seller
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    async with eng.begin() as conn:
        for price in (3_000_000, 1_000_000, 2_000_000, 5_000_000, 4_000_000):
            await conn.execute(
                text(
                    "INSERT INTO listings (id, seller_id, modification_id, mark_id, "
                    "model_id, year, price, mileage, color_id, condition, city_id, "
                    "status, license_plate_edit_count, viewing_enabled, published_at) "
                    "VALUES (gen_random_uuid(), :s, 'M1', 'BMW', 'BMW_5', 2019, :p, "
                    "1, 'black', 'good', '7700000000000', 'active', 0, false, now())"
                ),
                {"s": user_id, "p": price},
            )
    await eng.dispose()

    page1 = await committed_client.get(
        "/api/v1/listings", params={"sort": "price_asc", "limit": 2}
    )
    prices1 = [r["price"] for r in page1.json()["items"]]
    assert prices1 == sorted(prices1)

    page2 = await committed_client.get(
        "/api/v1/listings",
        params={"sort": "price_asc", "limit": 2, "cursor": page1.json()["next_cursor"]},
    )
    prices2 = [r["price"] for r in page2.json()["items"]]
    assert prices2 == sorted(prices2)
    assert min(prices2) >= max(prices1)


@pytest.mark.asyncio
async def test_get_listing_masking_owner_vs_anonymous(
    committed_client: AsyncClient, seller
):
    _, headers = seller
    listing_id = (
        await committed_client.post(
            "/api/v1/listings",
            json=_payload(
                vin="WBA12345678901234",
                sale_address="Москва, ул. Пример, 1",
                accepts_cash=True,
            ),
            headers=headers,
        )
    ).json()["id"]

    anon = (await committed_client.get(f"/api/v1/listings/{listing_id}")).json()
    assert anon["vin"] == "***************34"
    assert "sale_address" not in anon

    owner = (
        await committed_client.get(f"/api/v1/listings/{listing_id}", headers=headers)
    ).json()
    assert owner["vin"] == "WBA12345678901234"
    assert owner["sale_address"] == "Москва, ул. Пример, 1"


@pytest.mark.asyncio
async def test_publish_gating_payment_pref(
    committed_client: AsyncClient, seller, pg_container
):
    _, headers = seller
    listing_id = (
        await committed_client.post(
            "/api/v1/listings",
            json=_payload(vin="WBA99999999999934"),
            headers=headers,
        )
    ).json()["id"]

    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO listing_images (id, listing_id, url, thumbnail_url, "
                "is_primary, sort_order) VALUES "
                "(gen_random_uuid(), :lid, 'u', 't', true, 0)"
            ),
            {"lid": listing_id},
        )
    await eng.dispose()

    # no payment preference yet → 422
    r = await committed_client.post(
        f"/api/v1/listings/{listing_id}/publish", headers=headers
    )
    assert r.status_code == 422, r.text

    await committed_client.patch(
        f"/api/v1/listings/{listing_id}",
        json={"accepts_transfer": True},
        headers=headers,
    )
    r2 = await committed_client.post(
        f"/api/v1/listings/{listing_id}/publish", headers=headers
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["status"] == "pending_review"
