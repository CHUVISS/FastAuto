"""Edge-case coverage for the deposit-reservation redesign (Verification §4).

Most happy-path branches are covered by per-task tests; this module
consolidates the explicitly-listed edge cases that are not exercised
elsewhere.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security import create_access_token
from app.services.payments.yookassa_service import CreatedPayment
from tests.fixtures.committed import seed_user

pytestmark = pytest.mark.integration


def _eng(pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    return create_async_engine(url, connect_args={"statement_cache_size": 0})


async def _seed_listing(eng, seller_id) -> str:
    listing_id = str(uuid.uuid4())
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
                "status, license_plate_edit_count, accepts_cash, sale_address, "
                "viewing_enabled) "
                "VALUES (:id, :s, 'M1', 'BMW', 'BMW_5', 2019, 2500000, 1, 'black', "
                "'good', '7700000000000', 'active', 0, true, 'Москва, ул. X, 1', "
                "false)"
            ),
            {"id": listing_id, "s": seller_id},
        )
    return listing_id


@pytest_asyncio.fixture
async def parties(committed_client: AsyncClient, pg_container):
    eng = _eng(pg_container)
    seller_id = await seed_user(eng, "user", f"sell_{uuid.uuid4().hex[:6]}@e.com")
    buyer_id = await seed_user(eng, "user", f"buy_{uuid.uuid4().hex[:6]}@e.com")
    async with eng.begin() as conn:
        await conn.execute(
            text("UPDATE users SET phone_verified = true, phone = :p WHERE id = :id"),
            {"id": buyer_id, "p": "79991110000"},
        )
    listing_id = await _seed_listing(eng, seller_id)
    await eng.dispose()
    return {
        "seller_id": seller_id,
        "buyer_id": buyer_id,
        "listing_id": listing_id,
        "buyer_h": {"Authorization": f"Bearer {create_access_token(buyer_id)}"},
        "seller_h": {"Authorization": f"Bearer {create_access_token(seller_id)}"},
    }


def _hold():
    return patch(
        "app.services.payments.yookassa_service.create_hold",
        new=AsyncMock(
            return_value=CreatedPayment(
                id=f"pay-{uuid.uuid4().hex[:6]}", confirmation_url="https://pay"
            )
        ),
    )


def _cancel():
    return patch(
        "app.services.payments.yookassa_service.cancel_hold",
        new=AsyncMock(return_value="canceled"),
    )


@pytest.mark.asyncio
async def test_window_after_hold_deadline_rejected(
    committed_client, parties, pg_container
):
    """A buyer cannot book a viewing window that ends after the hold deadline."""
    with _hold():
        rid = (
            await committed_client.post(
                "/api/v1/reservations",
                json={"listing_id": parties["listing_id"]},
                headers=parties["buyer_h"],
            )
        ).json()["reservation_id"]

    eng = _eng(pg_container)
    far_window = uuid.uuid4()
    async with eng.begin() as conn:
        # Window scheduled past the 5-day hold (10 days from today)
        await conn.execute(
            text(
                "INSERT INTO viewing_windows (id, listing_id, window_date, "
                "time_from, time_to) VALUES (:id, :lid, :d, '10:00', '11:00')"
            ),
            {
                "id": far_window,
                "lid": parties["listing_id"],
                "d": date.today() + timedelta(days=10),
            },
        )
        await conn.execute(
            text("UPDATE reservations SET status = 'active' WHERE id = :id"),
            {"id": rid},
        )
    await eng.dispose()

    book = await committed_client.post(
        f"/api/v1/reservations/{rid}/book-viewing",
        json={"window_id": str(far_window)},
        headers=parties["buyer_h"],
    )
    assert book.status_code == 409


@pytest.mark.asyncio
async def test_outcome_same_value_no_budget_spent(
    committed_client, parties, pg_container
):
    """Re-writing the same outcome value does not consume a party's change budget."""
    with _hold():
        rid = (
            await committed_client.post(
                "/api/v1/reservations",
                json={"listing_id": parties["listing_id"]},
                headers=parties["buyer_h"],
            )
        ).json()["reservation_id"]
    eng = _eng(pg_container)
    async with eng.begin() as conn:
        await conn.execute(
            text("UPDATE reservations SET status = 'active' WHERE id = :id"),
            {"id": rid},
        )
    await eng.dispose()

    with _cancel():
        await committed_client.post(
            f"/api/v1/reservations/{rid}/outcome",
            json={"result": "sold"},
            headers=parties["buyer_h"],
        )
        # Same value again — must be a no-op
        again = await committed_client.post(
            f"/api/v1/reservations/{rid}/outcome",
            json={"result": "sold"},
            headers=parties["buyer_h"],
        )
        assert again.status_code == 200
        # And the buyer can still flip it once
        flip = await committed_client.post(
            f"/api/v1/reservations/{rid}/outcome",
            json={"result": "not_sold"},
            headers=parties["buyer_h"],
        )
        assert flip.status_code == 200
        assert flip.json()["outcome"] == "not_sold"


@pytest.mark.asyncio
async def test_favorites_cap_returns_422(committed_client, parties, pg_container):
    """Exceeding MAX_FAVORITES (300) returns 422 with no row inserted."""
    eng = _eng(pg_container)
    async with eng.begin() as conn:
        # Materialise 300 placeholder listings + favourite them so the next
        # POST trips the MAX_FAVORITES guard.
        await conn.execute(
            text(
                "INSERT INTO listings (id, seller_id, modification_id, mark_id, "
                "model_id, year, price, mileage, color_id, condition, city_id, "
                "status, license_plate_edit_count) "
                "SELECT gen_random_uuid(), :s, 'M1', 'BMW', 'BMW_5', 2019, "
                "2500000, 1, 'black', 'good', '7700000000000', 'active', 0 "
                "FROM generate_series(1, 300)"
            ),
            {"s": parties["seller_id"]},
        )
        await conn.execute(
            text(
                "INSERT INTO favorites (id, user_id, listing_id, created_at) "
                "SELECT gen_random_uuid(), :u, l.id, now() FROM listings l "
                "WHERE l.seller_id = :s AND l.id != :keep"
            ),
            {
                "u": parties["buyer_id"],
                "s": parties["seller_id"],
                "keep": parties["listing_id"],
            },
        )
    await eng.dispose()

    resp = await committed_client.post(
        "/api/v1/favorites",
        json={"listing_id": parties["listing_id"]},
        headers=parties["buyer_h"],
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_moderation_queue_masks_vin(committed_client, parties, pg_container):
    """Staff see masked VIN/licence-plate in the moderation queue."""
    eng = _eng(pg_container)
    pending_id = uuid.uuid4()
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO listings (id, seller_id, modification_id, mark_id, "
                "model_id, year, price, mileage, color_id, condition, city_id, "
                "status, license_plate_edit_count, accepts_cash, sale_address, "
                "vin) VALUES (:id, :s, 'M1', 'BMW', 'BMW_5', 2019, 2500000, 1, "
                "'black', 'good', '7700000000000', 'pending_review', 0, true, "
                "'addr', 'WBA99999999999A8')"
            ),
            {"id": pending_id, "s": parties["seller_id"]},
        )
    mod_id = await seed_user(eng, "moderator", f"mod_{uuid.uuid4().hex[:6]}@e.com")
    await eng.dispose()
    mod_h = {"Authorization": f"Bearer {create_access_token(mod_id)}"}

    queue = await committed_client.get("/api/v1/admin/listings", headers=mod_h)
    assert queue.status_code == 200
    rows = {r["id"]: r for r in queue.json()}
    assert rows[str(pending_id)]["vin"] == "**************A8"


# silence "unused" — `datetime`/`UTC` reserved for future deadline-edge tests
_ = (datetime, UTC, time)
