import pytest

from app.models.listings import Listing, ViewingBooking

pytestmark = pytest.mark.unit


def test_listing_has_sale_address_and_payment_prefs():
    cols = Listing.__table__.columns
    assert "sale_address" in cols
    assert cols["sale_address"].nullable is True
    assert cols["accepts_cash"].default.arg is False
    assert cols["accepts_transfer"].default.arg is False


def test_viewing_booking_has_reservation_fk():
    cols = ViewingBooking.__table__.columns
    assert "reservation_id" in cols
    fk = next(iter(cols["reservation_id"].foreign_keys))
    assert fk.target_fullname == "reservations.id"
