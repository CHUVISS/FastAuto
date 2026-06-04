from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest

from app.models.listings import ViewingWindow
from app.models.reservations import Reservation, ReservationStatus
from app.services.viewings import booking_service as svc

pytestmark = pytest.mark.unit


def _reservation(
    listing_id: uuid.UUID,
    *,
    status: ReservationStatus = ReservationStatus.active,
    hold_days: int = 5,
) -> Reservation:
    now = datetime.now(UTC)
    return Reservation(
        listing_id=listing_id,
        buyer_id=uuid.uuid4(),
        seller_id=uuid.uuid4(),
        deposit_amount=5000,
        status=status,
        payment_deadline=now + timedelta(minutes=30),
        hold_deadline=now + timedelta(days=hold_days),
    )


def _window(listing_id: uuid.UUID, *, day_offset: int = 1) -> ViewingWindow:
    return ViewingWindow(
        listing_id=listing_id,
        window_date=date.today() + timedelta(days=day_offset),
        time_from=time(10, 0),
        time_to=time(11, 0),
    )


def test_assert_can_book_active_reservation_inside_hold_succeeds():
    lid = uuid.uuid4()
    svc.assert_can_book(_reservation(lid), _window(lid), now=datetime.now(UTC))


def test_assert_can_book_foreign_window_throws():
    res = _reservation(uuid.uuid4())
    foreign = _window(uuid.uuid4())

    with pytest.raises(svc.BookingError, match="does not belong"):
        svc.assert_can_book(res, foreign, now=datetime.now(UTC))


def test_assert_can_book_window_after_hold_deadline_throws():
    lid = uuid.uuid4()
    res = _reservation(lid, hold_days=2)
    too_late = _window(lid, day_offset=5)

    with pytest.raises(svc.BookingError, match="after the reservation hold"):
        svc.assert_can_book(res, too_late, now=datetime.now(UTC))
