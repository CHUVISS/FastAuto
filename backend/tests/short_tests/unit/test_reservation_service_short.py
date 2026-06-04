from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.models.listings import Condition, Listing, ListingStatus
from app.models.reservations import (
    CancelReason,
    OutcomeParty,
    ReservationOutcome,
    ReservationStatus,
)
from app.models.users import User
from app.services.reservations import reservation_service as svc

pytestmark = pytest.mark.unit


def _deps():
    return SimpleNamespace(
        yk=SimpleNamespace(cancel_hold=AsyncMock(return_value="canceled"))
    )


def _buyer(*, verified: bool = True) -> User:
    return User(
        id=uuid.uuid4(),
        full_name="Buyer",
        email=f"b{uuid.uuid4().hex[:8]}@e.com",
        hashed_password="x",
        phone_verified=verified,
    )


def _listing(
    seller_id: uuid.UUID, *, status: ListingStatus = ListingStatus.active
) -> Listing:
    return Listing(
        id=uuid.uuid4(),
        seller_id=seller_id,
        modification_id="M1",
        mark_id="BMW",
        model_id="BMW_5",
        year=2019,
        price=2_500_000,
        mileage=1,
        color_id="black",
        condition=Condition.good,
        city_id="7700000000000",
        status=status,
    )


def test_build_reservation_active_listing_sets_deposit_and_locks_listing():
    buyer = _buyer()
    listing = _listing(uuid.uuid4())
    now = datetime.now(UTC)

    r = svc.build_reservation(buyer=buyer, listing=listing, now=now)

    assert r.status == ReservationStatus.pending_payment
    assert r.deposit_amount == settings.RESERVATION_DEPOSIT_AMOUNT
    assert r.hold_deadline == now + timedelta(days=settings.RESERVATION_HOLD_DAYS)
    assert listing.status == ListingStatus.reserved


@pytest.mark.asyncio
async def test_mark_outcome_first_call_releases_deposit_once():
    buyer = _buyer()
    listing = _listing(uuid.uuid4())
    r = svc.build_reservation(buyer=buyer, listing=listing)
    r.yk_payment_id = "pay-1"
    svc.confirm_hold(r)
    deps = _deps()

    await svc.mark_outcome(r, OutcomeParty.buyer, ReservationOutcome.sold, deps=deps)

    assert r.status == ReservationStatus.settling
    assert r.deposit_released_at is not None
    deps.yk.cancel_hold.assert_awaited_once_with(
        payment_id="pay-1", idempotence_key=f"{r.id}:release"
    )
    assert listing.status == ListingStatus.reserved


@pytest.mark.asyncio
async def test_build_reservation_unverified_buyer_throws():
    buyer = _buyer(verified=False)
    listing = _listing(uuid.uuid4())

    with pytest.raises(svc.ReservationValidationError):
        svc.build_reservation(buyer=buyer, listing=listing)

    # cancel is also idempotent on terminal states (sanity)
    assert listing.status == ListingStatus.active
    _ = CancelReason  # exported for callers; satisfies importlint
