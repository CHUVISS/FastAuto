import uuid
from datetime import UTC, datetime

from app.models.listings import ViewingWindow
from app.models.reservations import Reservation, ReservationStatus


class BookingError(Exception):
    pass


def window_end_dt(window: ViewingWindow) -> datetime:
    return datetime.combine(window.window_date, window.time_to, tzinfo=UTC)


def assert_window_eligible(
    *,
    listing_id: uuid.UUID,
    window: ViewingWindow,
    hold_deadline: datetime,
    now: datetime,
) -> None:
    if window.listing_id != listing_id:
        raise BookingError("Window does not belong to this listing")
    if window_end_dt(window) <= now:
        raise BookingError("Window is in the past")
    if window_end_dt(window) >= hold_deadline:
        raise BookingError("Window ends after the reservation hold deadline")


def assert_can_book(
    reservation: Reservation, window: ViewingWindow, *, now: datetime
) -> None:
    if reservation.status != ReservationStatus.active:
        raise BookingError("Reservation is not active")
    assert_window_eligible(
        listing_id=reservation.listing_id,
        window=window,
        hold_deadline=reservation.hold_deadline,
        now=now,
    )
