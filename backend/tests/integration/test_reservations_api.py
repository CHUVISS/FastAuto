import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security import create_access_token
from app.services.payments.yookassa_service import CreatedPayment
from tests.fixtures.committed import seed_user

pytestmark = pytest.mark.integration


async def _engine(pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    return create_async_engine(url, connect_args={"statement_cache_size": 0})


async def _seed_active_listing(eng, seller_id, *, hold_days_window=1) -> str:
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
                "license_plate_edit_count, sale_address, accepts_cash, viewing_enabled) "
                "VALUES (:id, :s, 'M1', 'BMW', 'BMW_5', 2019, 2500000, 1, 'black', 'good', "
                "'7700000000000', 'active', 0, 'Москва, ул. X, 1', true, true)"
            ),
            {"id": listing_id, "s": seller_id},
        )
    return listing_id


async def _seed_window(eng, listing_id, *, day_offset=1) -> str:
    window_id = str(uuid.uuid4())
    wdate = date.today() + timedelta(days=day_offset)
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO viewing_windows (id, listing_id, window_date, time_from, time_to) "
                "VALUES (:id, :lid, :d, '10:00', '11:00')"
            ),
            {"id": window_id, "lid": listing_id, "d": wdate},
        )
    return window_id


async def _verify_phone(eng, user_id, phone: str = "79991234567") -> None:
    async with eng.begin() as conn:
        await conn.execute(
            text("UPDATE users SET phone_verified = true, phone = :p WHERE id = :id"),
            {"id": user_id, "p": phone},
        )


@pytest_asyncio.fixture
async def parties(committed_client: AsyncClient, pg_container):
    eng = await _engine(pg_container)
    seller_id = await seed_user(eng, "user", f"seller_{uuid.uuid4().hex[:6]}@e.com")
    buyer_id = await seed_user(eng, "user", f"buyer_{uuid.uuid4().hex[:6]}@e.com")
    await _verify_phone(eng, buyer_id)
    listing_id = await _seed_active_listing(eng, seller_id)
    window_id = await _seed_window(eng, listing_id)
    await eng.dispose()
    buyer_headers = {"Authorization": f"Bearer {create_access_token(buyer_id)}"}
    seller_headers = {"Authorization": f"Bearer {create_access_token(seller_id)}"}
    return {
        "seller_id": seller_id,
        "buyer_id": buyer_id,
        "listing_id": listing_id,
        "window_id": window_id,
        "buyer_headers": buyer_headers,
        "seller_headers": seller_headers,
        "pg": pg_container,
    }


def _hold_patch():
    return patch(
        "app.services.payments.yookassa_service.create_hold",
        new=AsyncMock(
            return_value=CreatedPayment(id="pay-1", confirmation_url="https://pay")
        ),
    )


def _cancel_patch():
    return patch(
        "app.services.payments.yookassa_service.cancel_hold",
        new=AsyncMock(return_value="canceled"),
    )


@pytest.mark.asyncio
async def test_reserve_locks_listing(committed_client, parties):
    with _hold_patch() as hold:
        resp = await committed_client.post(
            "/api/v1/reservations",
            json={
                "listing_id": parties["listing_id"],
                "window_id": parties["window_id"],
            },
            headers=parties["buyer_headers"],
        )
    assert resp.status_code == 201, resp.text
    assert resp.json()["payment_url"] == "https://pay"
    hold.assert_awaited_once()

    detail = await committed_client.get(f"/api/v1/listings/{parties['listing_id']}")
    assert detail.json()["status"] == "reserved"


@pytest.mark.asyncio
async def test_reserve_own_listing_rejected(committed_client, parties):
    with _hold_patch():
        resp = await committed_client.post(
            "/api/v1/reservations",
            json={
                "listing_id": parties["listing_id"],
                "window_id": parties["window_id"],
            },
            headers=parties["seller_headers"],
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_duplicate_reserve_conflicts(committed_client, parties, pg_container):
    eng = await _engine(pg_container)
    other_id = await seed_user(eng, "user", f"other_{uuid.uuid4().hex[:6]}@e.com")
    await _verify_phone(eng, other_id, phone="79997654321")
    await eng.dispose()
    other_headers = {"Authorization": f"Bearer {create_access_token(other_id)}"}

    with _hold_patch():
        first = await committed_client.post(
            "/api/v1/reservations",
            json={
                "listing_id": parties["listing_id"],
                "window_id": parties["window_id"],
            },
            headers=parties["buyer_headers"],
        )
        assert first.status_code == 201
        second = await committed_client.post(
            "/api/v1/reservations",
            json={
                "listing_id": parties["listing_id"],
                "window_id": parties["window_id"],
            },
            headers=other_headers,
        )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_idempotent_reserve_same_buyer(committed_client, parties):
    find = MagicMock(confirmation=MagicMock(confirmation_url="https://pay"))
    with (
        _hold_patch(),
        patch(
            "app.services.payments.yookassa_service.find_payment",
            new=AsyncMock(return_value=find),
        ),
    ):
        r1 = await committed_client.post(
            "/api/v1/reservations",
            json={
                "listing_id": parties["listing_id"],
                "window_id": parties["window_id"],
            },
            headers=parties["buyer_headers"],
        )
        r2 = await committed_client.post(
            "/api/v1/reservations",
            json={
                "listing_id": parties["listing_id"],
                "window_id": parties["window_id"],
            },
            headers=parties["buyer_headers"],
        )
    assert r1.status_code == 201 and r2.status_code == 201
    assert r1.json()["reservation_id"] == r2.json()["reservation_id"]


@pytest.mark.asyncio
async def test_reserve_recovers_when_yk_payment_id_missing(
    committed_client, parties, pg_container
):
    with _hold_patch():
        first = await committed_client.post(
            "/api/v1/reservations",
            json={
                "listing_id": parties["listing_id"],
                "window_id": parties["window_id"],
            },
            headers=parties["buyer_headers"],
        )
    assert first.status_code == 201
    rid = first.json()["reservation_id"]

    eng = await _engine(pg_container)
    async with eng.begin() as conn:
        await conn.execute(
            text("UPDATE reservations SET yk_payment_id = NULL WHERE id = :id"),
            {"id": rid},
        )
    await eng.dispose()

    recovery_hold = patch(
        "app.services.payments.yookassa_service.create_hold",
        new=AsyncMock(
            return_value=CreatedPayment(
                id="pay-recovered", confirmation_url="https://pay/recovered"
            )
        ),
    )
    with recovery_hold as hold:
        retry = await committed_client.post(
            "/api/v1/reservations",
            json={
                "listing_id": parties["listing_id"],
                "window_id": parties["window_id"],
            },
            headers=parties["buyer_headers"],
        )

    assert retry.status_code == 201
    assert retry.json()["reservation_id"] == rid
    assert retry.json()["payment_url"] == "https://pay/recovered"
    hold.assert_awaited_once()
    assert hold.await_args.kwargs["idempotence_key"] == f"{rid}:hold"

    eng = await _engine(pg_container)
    async with eng.connect() as conn:
        stored = (
            await conn.execute(
                text("SELECT yk_payment_id FROM reservations WHERE id = :id"),
                {"id": rid},
            )
        ).scalar_one()
    await eng.dispose()
    assert stored == "pay-recovered"


async def _reserve_and_confirm(committed_client, parties, pg_container):
    with _hold_patch():
        rid = (
            await committed_client.post(
                "/api/v1/reservations",
                json={
                    "listing_id": parties["listing_id"],
                    "window_id": parties["window_id"],
                },
                headers=parties["buyer_headers"],
            )
        ).json()["reservation_id"]
    eng = await _engine(pg_container)
    async with eng.begin() as conn:
        await conn.execute(
            text("UPDATE reservations SET status = 'active' WHERE id = :id"),
            {"id": rid},
        )
    await eng.dispose()
    return rid


@pytest.mark.asyncio
async def test_book_viewing(committed_client, parties, pg_container):
    rid = await _reserve_and_confirm(committed_client, parties, pg_container)
    eng = await _engine(pg_container)
    window_id = await _seed_window(eng, parties["listing_id"], day_offset=2)
    await eng.dispose()
    resp = await committed_client.post(
        f"/api/v1/reservations/{rid}/book-viewing",
        json={"window_id": window_id},
        headers=parties["buyer_headers"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["booked"] is True


@pytest.mark.asyncio
async def test_outcome_first_mark_settles_and_releases(
    committed_client, parties, pg_container
):
    rid = await _reserve_and_confirm(committed_client, parties, pg_container)
    with _cancel_patch() as cancel:
        resp = await committed_client.post(
            f"/api/v1/reservations/{rid}/outcome",
            json={"result": "sold"},
            headers=parties["buyer_headers"],
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "settling"
    cancel.assert_awaited_once()


@pytest.mark.asyncio
async def test_decline_requires_reason(committed_client, parties, pg_container):
    rid = await _reserve_and_confirm(committed_client, parties, pg_container)
    bad = await committed_client.post(
        f"/api/v1/reservations/{rid}/decline",
        json={"reason": ""},
        headers=parties["seller_headers"],
    )
    assert bad.status_code == 422

    with _cancel_patch():
        ok = await committed_client.post(
            f"/api/v1/reservations/{rid}/decline",
            json={"reason": "Машина уже продана"},
            headers=parties["seller_headers"],
        )
    assert ok.status_code == 200
    assert ok.json()["status"] == "cancelled"
    detail = await committed_client.get(f"/api/v1/listings/{parties['listing_id']}")
    assert detail.json()["status"] == "active"
