from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.short_tests._helpers import (
    activate_reservation,
    auth_headers,
    cancel_patch,
    hold_patch,
    seed_active_listing,
    seed_role,
    verify_phone,
)

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_reserve_confirm_mark_outcome_settles_and_releases_deposit(
    committed_client: AsyncClient, pg_container
):
    seller_id, _ = await seed_role(pg_container, role="user")
    buyer_id, buyer_h = await seed_role(pg_container, role="user")
    await verify_phone(pg_container, buyer_id)
    listing_id = await seed_active_listing(pg_container, seller_id)

    with hold_patch():
        reserve = await committed_client.post(
            "/api/v1/reservations", json={"listing_id": listing_id}, headers=buyer_h
        )
    assert reserve.status_code == 201
    rid = reserve.json()["reservation_id"]
    assert reserve.json()["payment_url"] == "https://pay"

    detail = await committed_client.get(f"/api/v1/listings/{listing_id}")
    assert detail.json()["status"] == "reserved"

    await activate_reservation(pg_container, rid)
    revealed = await committed_client.get(
        f"/api/v1/reservations/{rid}", headers=buyer_h
    )
    assert revealed.json()["status"] == "active"
    assert revealed.json()["sale_address"]

    with cancel_patch():
        outcome = await committed_client.post(
            f"/api/v1/reservations/{rid}/outcome",
            json={"result": "sold"},
            headers=buyer_h,
        )
    assert outcome.status_code == 200
    assert outcome.json()["status"] == "settling"


@pytest.mark.asyncio
async def test_reserve_own_listing_returns_unprocessable(
    committed_client: AsyncClient, pg_container
):
    seller_id, seller_h = await seed_role(pg_container, role="user")
    await verify_phone(pg_container, seller_id)
    listing_id = await seed_active_listing(pg_container, seller_id)

    with hold_patch():
        response = await committed_client.post(
            "/api/v1/reservations",
            json={"listing_id": listing_id},
            headers=auth_headers(seller_id),
        )

    assert response.status_code == 422
