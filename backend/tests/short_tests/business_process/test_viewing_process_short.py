from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.short_tests._helpers import (
    activate_reservation,
    cancel_patch,
    hold_patch,
    seed_active_listing,
    seed_role,
    seed_window,
    verify_phone,
)

pytestmark = pytest.mark.integration


async def _reserve_active(committed_client, pg_container) -> tuple[str, str, dict]:
    seller_id, seller_h = await seed_role(pg_container, role="user")
    buyer_id, buyer_h = await seed_role(pg_container, role="user")
    await verify_phone(pg_container, buyer_id)
    listing_id = await seed_active_listing(pg_container, seller_id)
    with hold_patch():
        rid = (
            await committed_client.post(
                "/api/v1/reservations", json={"listing_id": listing_id}, headers=buyer_h
            )
        ).json()["reservation_id"]
    await activate_reservation(pg_container, rid)
    return rid, listing_id, {"buyer": buyer_h, "seller": seller_h}


@pytest.mark.asyncio
async def test_book_viewing_inside_hold_succeeds(
    committed_client: AsyncClient, pg_container
):
    rid, listing_id, h = await _reserve_active(committed_client, pg_container)
    window_id = await seed_window(pg_container, listing_id, day_offset=1)

    response = await committed_client.post(
        f"/api/v1/reservations/{rid}/book-viewing",
        json={"window_id": window_id},
        headers=h["buyer"],
    )

    assert response.status_code == 200
    assert response.json()["booked"] is True


@pytest.mark.asyncio
async def test_book_viewing_after_hold_deadline_rejected(
    committed_client: AsyncClient, pg_container
):
    rid, listing_id, h = await _reserve_active(committed_client, pg_container)
    far_window = await seed_window(pg_container, listing_id, day_offset=30)

    response = await committed_client.post(
        f"/api/v1/reservations/{rid}/book-viewing",
        json={"window_id": far_window},
        headers=h["buyer"],
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_seller_decline_releases_and_frees_listing(
    committed_client: AsyncClient, pg_container
):
    rid, listing_id, h = await _reserve_active(committed_client, pg_container)

    with cancel_patch():
        decline = await committed_client.post(
            f"/api/v1/reservations/{rid}/decline",
            json={"reason": "Машина уже продана"},
            headers=h["seller"],
        )

    assert decline.status_code == 200
    assert decline.json()["status"] == "cancelled"
    detail = await committed_client.get(f"/api/v1/listings/{listing_id}")
    assert detail.json()["status"] == "active"
