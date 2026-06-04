import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from app.crud import reservations as res_crud
from app.models.reservations import Reservation, ReservationOutcome, ReservationStatus

pytestmark = pytest.mark.integration


async def _seed_listing(db_session, seller_id) -> uuid.UUID:
    await db_session.execute(
        text(
            "INSERT INTO catalog.modifications (id) VALUES ('M1') ON CONFLICT DO NOTHING"
        )
    )
    listing_id = uuid.uuid4()
    await db_session.execute(
        text(
            "INSERT INTO listings (id, seller_id, modification_id, mark_id, model_id, "
            "year, price, mileage, color_id, condition, city_id, status, "
            "license_plate_edit_count, accepts_cash, accepts_transfer) VALUES "
            "(:id, :s, 'M1', 'BMW', 'BMW_5', 2019, 2500000, 1, 'black', 'good', "
            "'7700000000000', 'reserved', 0, true, false)"
        ),
        {"id": listing_id, "s": str(seller_id)},
    )
    await db_session.flush()
    return listing_id


def _res(buyer, seller, listing_id, **over) -> Reservation:
    now = datetime.now(UTC)
    base = {
        "listing_id": listing_id,
        "buyer_id": buyer,
        "seller_id": seller,
        "deposit_amount": 5000,
        "status": ReservationStatus.pending_payment,
        "payment_deadline": now + timedelta(minutes=30),
        "hold_deadline": now + timedelta(days=5),
    }
    base.update(over)
    return Reservation(**base)


@pytest.mark.asyncio
async def test_create_get_and_by_payment(db_session, regular_user, admin_user):
    listing_id = await _seed_listing(db_session, admin_user.id)
    r = _res(regular_user.id, admin_user.id, listing_id, yk_payment_id="pay-1")
    await res_crud.create(db_session, r)
    await db_session.flush()

    assert (await res_crud.get(db_session, r.id)).id == r.id
    assert (await res_crud.get_by_payment(db_session, "pay-1")).id == r.id


@pytest.mark.asyncio
async def test_has_active_reservation(db_session, regular_user, admin_user):
    listing_id = await _seed_listing(db_session, admin_user.id)
    assert await res_crud.has_active_reservation(db_session, listing_id) is False
    r = _res(regular_user.id, admin_user.id, listing_id)
    await res_crud.create(db_session, r)
    await db_session.flush()
    assert await res_crud.has_active_reservation(db_session, listing_id) is True
    assert (await res_crud.get_active_for_listing(db_session, listing_id)).id == r.id

    r.status = ReservationStatus.cancelled
    await db_session.flush()
    assert await res_crud.has_active_reservation(db_session, listing_id) is False


@pytest.mark.asyncio
async def test_list_for_user(db_session, regular_user, admin_user):
    listing_id = await _seed_listing(db_session, admin_user.id)
    r = _res(regular_user.id, admin_user.id, listing_id)
    await res_crud.create(db_session, r)
    await db_session.flush()
    buyer_rows = await res_crud.list_for_user(db_session, regular_user.id)
    seller_rows = await res_crud.list_for_user(db_session, admin_user.id)
    assert r.id in {x.id for x in buyer_rows}
    assert r.id in {x.id for x in seller_rows}


@pytest.mark.asyncio
async def test_scan_queries(db_session, regular_user, admin_user):
    listing_id = await _seed_listing(db_session, admin_user.id)
    now = datetime.now(UTC)

    expired_pending = _res(
        regular_user.id,
        admin_user.id,
        listing_id,
        status=ReservationStatus.pending_payment,
        payment_deadline=now - timedelta(minutes=1),
    )
    await res_crud.create(db_session, expired_pending)
    await db_session.flush()
    expired_ids = {r.id for r in await res_crud.list_expired_holds(db_session, now)}
    assert expired_pending.id in expired_ids

    expired_pending.status = ReservationStatus.cancelled
    settling = _res(
        regular_user.id,
        admin_user.id,
        listing_id,
        status=ReservationStatus.settling,
        outcome=ReservationOutcome.sold,
        correction_deadline=now - timedelta(minutes=1),
    )
    await res_crud.create(db_session, settling)
    await db_session.flush()
    due_ids = {r.id for r in await res_crud.list_settling_due(db_session, now)}
    assert settling.id in due_ids

    settling.status = ReservationStatus.cancelled
    active_no_prompt = _res(
        regular_user.id,
        admin_user.id,
        listing_id,
        status=ReservationStatus.active,
        last_prompt_at=None,
    )
    await res_crud.create(db_session, active_no_prompt)
    await db_session.flush()
    cand_ids = {
        r.id
        for r in await res_crud.list_prompt_candidates(
            db_session, now, timedelta(hours=24)
        )
    }
    assert active_no_prompt.id in cand_ids
