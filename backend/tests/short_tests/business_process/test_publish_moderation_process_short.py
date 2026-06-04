from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from tests.short_tests._helpers import auth_headers, engine, seed_role

pytestmark = pytest.mark.integration


def _create_payload(**over) -> dict:
    base = {
        "modification_id": "M1",
        "year": 2019,
        "price": 2_500_000,
        "mileage": 85_000,
        "color_id": "black",
        "condition": "good",
        "city_id": "7700000000000",
        "vin": f"WBA{uuid.uuid4().hex[:14].upper()}",
        "sale_address": "Москва, ул. Пример, 1",
        "accepts_cash": True,
        "viewing_enabled": True,
    }
    base.update(over)
    return base


async def _seed_catalog_and_image(pg_container, listing_id: str | None = None) -> None:
    eng = engine(pg_container)
    async with eng.begin() as conn:
        for stmt in [
            "INSERT INTO catalog.marks (id,name) VALUES ('BMW','BMW') ON CONFLICT DO NOTHING",
            "INSERT INTO catalog.models (id,mark_id,name) VALUES ('BMW_5','BMW','5') ON CONFLICT DO NOTHING",
            "INSERT INTO catalog.generations (id,model_id,name,year_from,year_to) "
            "VALUES ('G1','BMW_5','VII',2016,2023) ON CONFLICT DO NOTHING",
            "INSERT INTO catalog.modifications (id,mark_id,model_id,generation_id,name) "
            "VALUES ('M1','BMW','BMW_5','G1','3.0 AT') ON CONFLICT DO NOTHING",
        ]:
            await conn.execute(text(stmt))
        if listing_id is not None:
            await conn.execute(
                text(
                    "INSERT INTO listing_images (id, listing_id, url, thumbnail_url, "
                    "is_primary, sort_order) VALUES "
                    "(gen_random_uuid(), :lid, 'u', 't', true, 0)"
                ),
                {"lid": listing_id},
            )
            await conn.execute(
                text(
                    "INSERT INTO viewing_windows (id, listing_id, window_date, "
                    "time_from, time_to) VALUES "
                    "(gen_random_uuid(), :lid, CURRENT_DATE + 1, '10:00', '11:00')"
                ),
                {"lid": listing_id},
            )
    await eng.dispose()


@pytest.mark.asyncio
async def test_create_publish_approve_makes_listing_active(
    committed_client: AsyncClient, pg_container
):
    await _seed_catalog_and_image(pg_container)
    seller_id, seller_h = await seed_role(pg_container, role="user")
    _, mod_h = await seed_role(pg_container, role="moderator")

    created = await committed_client.post(
        "/api/v1/listings", json=_create_payload(), headers=seller_h
    )
    assert created.status_code == 201, created.text
    listing_id = created.json()["id"]
    await _seed_catalog_and_image(pg_container, listing_id)

    publish = await committed_client.post(
        f"/api/v1/listings/{listing_id}/publish", headers=seller_h
    )
    assert publish.status_code == 200
    assert publish.json()["status"] == "pending_review"

    approve = await committed_client.post(
        f"/api/v1/admin/listings/{listing_id}/approve", headers=mod_h
    )
    assert approve.status_code == 200
    assert approve.json()["status"] == "active"


@pytest.mark.asyncio
async def test_publish_without_payment_preference_returns_unprocessable(
    committed_client: AsyncClient, pg_container
):
    await _seed_catalog_and_image(pg_container)
    seller_id, seller_h = await seed_role(pg_container, role="user")

    created = await committed_client.post(
        "/api/v1/listings",
        json=_create_payload(accepts_cash=False, accepts_transfer=False),
        headers=seller_h,
    )
    assert created.status_code == 201
    listing_id = created.json()["id"]
    await _seed_catalog_and_image(pg_container, listing_id)

    publish = await committed_client.post(
        f"/api/v1/listings/{listing_id}/publish", headers=auth_headers(seller_id)
    )

    assert publish.status_code == 422
