"""End-to-end deposit-reservation flow (Verification §3 of the redesign plan).

Walks: seller publish (no payout method) → moderator approve → buyer reserve
→ payment.waiting_for_capture webhook → buyer sees seller phone + address
→ book viewing → outcome (buyer marks sold) → seller overrides to not_sold
→ correction window closes → finalize → completed + listing active.

All YooKassa calls are patched at the active-surface boundary so the test
never hits the network.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.services.payments.yookassa_service import CreatedPayment
from app.services.reservations.reservation_service import _Handlers
from tests.fixtures.committed import seed_user

pytestmark = pytest.mark.b2b


def _maker(pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    return eng, async_sessionmaker(eng, expire_on_commit=False)


async def _seed_catalog(eng):
    async with eng.begin() as conn:
        for stmt in [
            "INSERT INTO catalog.marks (id,name,popular) VALUES ('BMW','BMW',true) "
            "ON CONFLICT DO NOTHING",
            "INSERT INTO catalog.models (id,mark_id,name) VALUES ('BMW_5','BMW','5') "
            "ON CONFLICT DO NOTHING",
            "INSERT INTO catalog.generations (id,model_id,name,year_from,year_to) "
            "VALUES ('G1','BMW_5','VII',2016,2023) ON CONFLICT DO NOTHING",
            "INSERT INTO catalog.configurations (id,generation_id,body_type) "
            "VALUES ('C1','G1','SEDAN') ON CONFLICT DO NOTHING",
            "INSERT INTO catalog.modifications "
            "(id,mark_id,model_id,generation_id,configuration_id,name) "
            "VALUES ('M1','BMW','BMW_5','G1','C1','3.0 AT') ON CONFLICT DO NOTHING",
            "INSERT INTO catalog.specifications (id,engine_type) "
            "VALUES ('M1','Дизельный') ON CONFLICT DO NOTHING",
        ]:
            await conn.execute(text(stmt))


@pytest_asyncio.fixture
async def world(committed_client: AsyncClient, pg_container):
    eng, sm = _maker(pg_container)
    await _seed_catalog(eng)
    seller_id = await seed_user(eng, "user", f"sell_{uuid.uuid4().hex[:6]}@e.com")
    buyer_id = await seed_user(eng, "user", f"buy_{uuid.uuid4().hex[:6]}@e.com")
    mod_id = await seed_user(eng, "moderator", f"mod_{uuid.uuid4().hex[:6]}@e.com")
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "UPDATE users SET phone_verified = true, phone = '79991111111' "
                "WHERE id = :id"
            ),
            {"id": buyer_id},
        )
        await conn.execute(
            text(
                "UPDATE users SET phone = '79993333333', phone_visible = true "
                "WHERE id = :id"
            ),
            {"id": seller_id},
        )
    yield {
        "eng": eng,
        "sm": sm,
        "seller": seller_id,
        "buyer": buyer_id,
        "moderator": mod_id,
        "seller_h": {"Authorization": f"Bearer {create_access_token(seller_id)}"},
        "buyer_h": {"Authorization": f"Bearer {create_access_token(buyer_id)}"},
        "moderator_h": {"Authorization": f"Bearer {create_access_token(mod_id)}"},
    }
    await eng.dispose()


@pytest.mark.asyncio
async def test_full_reservation_flow(committed_client: AsyncClient, world):
    # 1) Seller creates a draft listing (with sale_address + accepts_cash).
    create = await committed_client.post(
        "/api/v1/listings",
        json={
            "modification_id": "M1",
            "year": 2019,
            "price": 2_500_000,
            "mileage": 85000,
            "color_id": "black",
            "condition": "good",
            "city_id": "7700000000000",
            "vin": "WBA12345678901234",
            "sale_address": "Москва, ул. Пример, 1",
            "accepts_cash": True,
            "viewing_enabled": True,
        },
        headers=world["seller_h"],
    )
    assert create.status_code == 201, create.text
    listing_id = create.json()["id"]

    # Seed image + future viewing window (within the 5-day hold).
    eng = world["eng"]
    window_id = uuid.uuid4()
    async with eng.begin() as conn:
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
                "time_from, time_to) VALUES (:id, :lid, :d, '10:00', '11:00')"
            ),
            {
                "id": window_id,
                "lid": listing_id,
                "d": date.today() + timedelta(days=2),
            },
        )

    # 2) Seller publishes (no payout method required).
    publish = await committed_client.post(
        f"/api/v1/listings/{listing_id}/publish", headers=world["seller_h"]
    )
    assert publish.status_code == 200, publish.text
    assert publish.json()["status"] == "pending_review"

    # 3) Moderator approves.
    approve = await committed_client.post(
        f"/api/v1/admin/listings/{listing_id}/approve", headers=world["moderator_h"]
    )
    assert approve.status_code == 200
    assert approve.json()["status"] == "active"

    # 4) Buyer reserves — two-stage hold (capture=false), no deal.
    fake_payment = CreatedPayment(id="pay-b2b-1", confirmation_url="https://pay")
    with patch(
        "app.services.payments.yookassa_service.create_hold",
        new=AsyncMock(return_value=fake_payment),
    ) as create_hold:
        reserve = await committed_client.post(
            "/api/v1/reservations",
            json={"listing_id": listing_id, "window_id": str(window_id)},
            headers=world["buyer_h"],
        )
    assert reserve.status_code == 201, reserve.text
    rid = reserve.json()["reservation_id"]
    assert reserve.json()["payment_url"] == "https://pay"
    payload = create_hold.call_args.kwargs
    assert payload["amount_rub"] == 5000

    detail = await committed_client.get(f"/api/v1/listings/{listing_id}")
    assert detail.json()["status"] == "reserved"

    # 5) Hold confirmed via webhook → reservation active + buyer sees phone+addr.
    handlers = _Handlers(world["sm"], MagicMock())
    with patch(
        "app.services.reservations.reservation_service.yk.find_payment",
        new=AsyncMock(return_value=MagicMock(status="waiting_for_capture")),
    ):
        await handlers.on_hold_confirmed("pay-b2b-1")

    revealed = await committed_client.get(
        f"/api/v1/reservations/{rid}", headers=world["buyer_h"]
    )
    body = revealed.json()
    assert body["status"] == "active"
    assert body["seller_phone"] == "79993333333"
    assert body["sale_address"] == "Москва, ул. Пример, 1"

    # 6) Buyer books the viewing window.
    book = await committed_client.post(
        f"/api/v1/reservations/{rid}/book-viewing",
        json={"window_id": str(window_id)},
        headers=world["buyer_h"],
    )
    assert book.status_code == 200, book.text

    # 7) Buyer marks sold → settling + release.
    with patch(
        "app.services.reservations.reservation_service.yk.cancel_hold",
        new=AsyncMock(return_value="canceled"),
    ) as cancel_hold:
        outcome = await committed_client.post(
            f"/api/v1/reservations/{rid}/outcome",
            json={"result": "sold"},
            headers=world["buyer_h"],
        )
    assert outcome.status_code == 200
    assert outcome.json() == {"status": "settling", "outcome": "sold"}
    cancel_hold.assert_awaited_once()

    # 8) Seller overrides to not_sold (one change allowed).
    override = await committed_client.post(
        f"/api/v1/reservations/{rid}/outcome",
        json={"result": "not_sold"},
        headers=world["seller_h"],
    )
    assert override.status_code == 200
    assert override.json()["outcome"] == "not_sold"

    # 9) Seller tries to flip back → locked.
    again = await committed_client.post(
        f"/api/v1/reservations/{rid}/outcome",
        json={"result": "sold"},
        headers=world["seller_h"],
    )
    assert again.status_code == 409

    # 10) Finalize after correction window closes (simulated via deadline shift).
    async with eng.begin() as conn:
        await conn.execute(
            text("UPDATE reservations SET correction_deadline = :d WHERE id = :id"),
            {"d": datetime.now(UTC) - timedelta(seconds=5), "id": rid},
        )
    from app.services import scheduler

    await scheduler.run_finalize_settling(session_factory=world["sm"])

    final_state = await committed_client.get(
        f"/api/v1/reservations/{rid}", headers=world["buyer_h"]
    )
    assert final_state.json()["status"] == "completed"

    # Listing back to active since outcome was not_sold (last write).
    after_listing = await committed_client.get(f"/api/v1/listings/{listing_id}")
    assert after_listing.json()["status"] == "active"

    # silence "unused" — `time` is needed to make timestamps stable in CI clocks
    _ = time
