import pytest
from sqlalchemy import BigInteger

from app.models.reservations import (
    CancelReason,
    OutcomeParty,
    Reservation,
    ReservationOutcome,
    ReservationStatus,
)

pytestmark = pytest.mark.unit


def test_status_enum_values():
    assert {s.value for s in ReservationStatus} == {
        "pending_payment",
        "active",
        "settling",
        "completed",
        "cancelled",
    }


def test_outcome_party_cancel_enums():
    assert {o.value for o in ReservationOutcome} == {"sold", "not_sold"}
    assert {p.value for p in OutcomeParty} == {"buyer", "seller"}
    assert {
        "buyer_cancelled",
        "seller_declined",
        "payment_abandoned",
        "hold_expired",
        "hold_released_externally",
        "admin",
    } <= {c.value for c in CancelReason}


def test_deposit_bigint_and_defaults():
    cols = Reservation.__table__.columns
    assert isinstance(cols["deposit_amount"].type, BigInteger)
    assert cols["status"].default.arg == ReservationStatus.pending_payment
    assert cols["buyer_change_used"].default.arg is False
    assert cols["seller_change_used"].default.arg is False


def test_partial_unique_and_scan_indexes():
    names = {ix.name for ix in Reservation.__table__.indexes}
    assert {
        "uniq_active_reservation_per_listing",
        "idx_reservation_hold_deadline",
        "idx_reservation_correction_deadline",
        "idx_reservation_prompt_scan",
    } <= names


def test_fk_targets():
    cols = Reservation.__table__.columns
    assert next(iter(cols["listing_id"].foreign_keys)).target_fullname == "listings.id"
    assert next(iter(cols["buyer_id"].foreign_keys)).target_fullname == "users.id"
    assert next(iter(cols["seller_id"].foreign_keys)).target_fullname == "users.id"
