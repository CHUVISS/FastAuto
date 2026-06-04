import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy import text

from app.crud import viewings as viewings_crud
from app.models.listings import BookingStatus, ViewingWindow
from app.models.reservations import Reservation, ReservationStatus

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
            "license_plate_edit_count) VALUES "
            "(:id, :s, 'M1', 'BMW', 'BMW_5', 2019, 2500000, 1, 'black', 'good', "
            "'7700000000000', 'reserved', 0)"
        ),
        {"id": listing_id, "s": str(seller_id)},
    )
    await db_session.flush()
    return listing_id


@pytest.mark.asyncio
async def test_booking_lifecycle(db_session, regular_user, admin_user):
    listing_id = await _seed_listing(db_session, admin_user.id)
    now = datetime.now(UTC)
    reservation = Reservation(
        listing_id=listing_id,
        buyer_id=regular_user.id,
        seller_id=admin_user.id,
        deposit_amount=5000,
        status=ReservationStatus.active,
        payment_deadline=now + timedelta(minutes=30),
        hold_deadline=now + timedelta(days=5),
    )
    db_session.add(reservation)
    window = ViewingWindow(
        listing_id=listing_id,
        window_date=date.today() + timedelta(days=1),
        time_from=time(10, 0),
        time_to=time(11, 0),
    )
    db_session.add(window)
    await db_session.flush()

    booking = await viewings_crud.create_booking(
        db_session,
        reservation_id=reservation.id,
        listing_id=listing_id,
        buyer_id=regular_user.id,
        window_id=window.id,
    )
    await db_session.flush()

    found = await viewings_crud.get_active_booking_for_reservation(
        db_session, reservation.id
    )
    assert found is not None and found.id == booking.id

    await viewings_crud.cancel_booking(booking)
    await db_session.flush()
    assert booking.status == BookingStatus.cancelled
    assert (
        await viewings_crud.get_active_booking_for_reservation(
            db_session, reservation.id
        )
        is None
    )
