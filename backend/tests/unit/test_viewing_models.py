import pytest

from app.models.listings import BookingStatus, ViewingBooking, ViewingWindow

pytestmark = pytest.mark.unit


def test_viewing_window_columns():
    cols = set(ViewingWindow.__table__.columns.keys())
    assert {
        "listing_id",
        "window_date",
        "time_from",
        "time_to",
        "is_available",
    } <= cols


def test_booking_status_values():
    assert {s.value for s in BookingStatus} == {"scheduled", "completed", "cancelled"}


def test_booking_partial_unique_active():
    index_names = {ix.name for ix in ViewingBooking.__table__.indexes}
    assert "uniq_active_booking" in index_names


def test_window_slot_unique():
    index_names = {ix.name for ix in ViewingWindow.__table__.indexes}
    assert "uniq_window_slot" in index_names
