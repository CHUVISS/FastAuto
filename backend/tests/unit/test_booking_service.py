import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest

from app.models.listings import ViewingWindow
from app.models.reservations import Reservation, ReservationStatus
from app.services.viewings import booking_service as svc

pytestmark = pytest.mark.unit


def _reservation(listing_id, *, status=ReservationStatus.active, hold_days=5):
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


def _window(listing_id, *, day_offset=1):
    return ViewingWindow(
        listing_id=listing_id,
        window_date=date.today() + timedelta(days=day_offset),
        time_from=time(10, 0),
        time_to=time(11, 0),
    )


def test_assert_can_book_ok():
    lid = uuid.uuid4()
    svc.assert_can_book(_reservation(lid), _window(lid), now=datetime.now(UTC))


def test_assert_can_book_rejects_non_active():
    lid = uuid.uuid4()
    r = _reservation(lid, status=ReservationStatus.pending_payment)
    with pytest.raises(svc.BookingError):
        svc.assert_can_book(r, _window(lid), now=datetime.now(UTC))


def test_assert_can_book_rejects_foreign_window():
    r = _reservation(uuid.uuid4())
    other_window = _window(uuid.uuid4())
    with pytest.raises(svc.BookingError):
        svc.assert_can_book(r, other_window, now=datetime.now(UTC))


def test_assert_can_book_rejects_window_after_hold_deadline():
    lid = uuid.uuid4()
    r = _reservation(lid, hold_days=2)
    late_window = _window(lid, day_offset=5)
    with pytest.raises(svc.BookingError):
        svc.assert_can_book(r, late_window, now=datetime.now(UTC))


def test_window_eligible_ok():
    lid = uuid.uuid4()
    now = datetime.now(UTC)
    svc.assert_window_eligible(
        listing_id=lid,
        window=_window(lid),
        hold_deadline=now + timedelta(days=5),
        now=now,
    )


def test_window_eligible_rejects_foreign_listing():
    now = datetime.now(UTC)
    with pytest.raises(svc.BookingError):
        svc.assert_window_eligible(
            listing_id=uuid.uuid4(),
            window=_window(uuid.uuid4()),
            hold_deadline=now + timedelta(days=5),
            now=now,
        )


def test_window_eligible_rejects_past_window():
    lid = uuid.uuid4()
    now = datetime.now(UTC)
    past = ViewingWindow(
        listing_id=lid,
        window_date=date.today() - timedelta(days=1),
        time_from=time(10, 0),
        time_to=time(11, 0),
    )
    with pytest.raises(svc.BookingError):
        svc.assert_window_eligible(
            listing_id=lid,
            window=past,
            hold_deadline=now + timedelta(days=5),
            now=now,
        )


def test_window_eligible_rejects_window_after_hold_deadline():
    lid = uuid.uuid4()
    now = datetime.now(UTC)
    late = _window(lid, day_offset=10)
    with pytest.raises(svc.BookingError):
        svc.assert_window_eligible(
            listing_id=lid,
            window=late,
            hold_deadline=now + timedelta(days=2),
            now=now,
        )
