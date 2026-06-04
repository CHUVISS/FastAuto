from __future__ import annotations

import pytest
from sqlalchemy import BigInteger

from app.models.reservations import Reservation, ReservationStatus

pytestmark = pytest.mark.unit


def test_status_enum_covers_full_lifecycle():
    assert {s.value for s in ReservationStatus} == {
        "pending_payment",
        "active",
        "settling",
        "completed",
        "cancelled",
    }


def test_deposit_amount_is_bigint_and_partial_unique_index_present():
    cols = Reservation.__table__.columns
    assert isinstance(cols["deposit_amount"].type, BigInteger)

    index_names = {ix.name for ix in Reservation.__table__.indexes}
    assert "uniq_active_reservation_per_listing" in index_names
