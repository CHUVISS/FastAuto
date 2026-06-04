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


def _buyer(*, verified=True):
    return User(
        id=uuid.uuid4(),
        full_name="Buyer",
        email=f"b{uuid.uuid4().hex[:8]}@e.com",
        hashed_password="x",
        phone_verified=verified,
    )


def _listing(seller_id, *, status=ListingStatus.active):
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


def test_build_reservation_ok():
    buyer = _buyer()
    listing = _listing(uuid.uuid4())
    now = datetime.now(UTC)
    r = svc.build_reservation(buyer=buyer, listing=listing, now=now)
    assert r.status == ReservationStatus.pending_payment
    assert r.deposit_amount == settings.RESERVATION_DEPOSIT_AMOUNT
    assert r.payment_deadline == now + timedelta(
        minutes=settings.DEPOSIT_PAYMENT_TTL_MINUTES
    )
    assert r.hold_deadline == now + timedelta(days=settings.RESERVATION_HOLD_DAYS)
    assert listing.status == ListingStatus.reserved


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b, ls: setattr(ls, "status", ListingStatus.draft),
        lambda b, ls: setattr(b, "phone_verified", False),
    ],
)
def test_build_reservation_rejects(mutate):
    buyer = _buyer()
    listing = _listing(uuid.uuid4())
    mutate(buyer, listing)
    with pytest.raises(svc.ReservationValidationError):
        svc.build_reservation(buyer=buyer, listing=listing)


def test_build_reservation_rejects_own_listing():
    buyer = _buyer()
    listing = _listing(buyer.id)
    with pytest.raises(svc.ReservationValidationError):
        svc.build_reservation(buyer=buyer, listing=listing)


def test_confirm_hold_transitions_and_idempotent():
    buyer = _buyer()
    listing = _listing(uuid.uuid4())
    r = svc.build_reservation(buyer=buyer, listing=listing)
    svc.confirm_hold(r)
    assert r.status == ReservationStatus.active
    svc.confirm_hold(r)  # idempotent
    assert r.status == ReservationStatus.active
    r.status = ReservationStatus.cancelled
    with pytest.raises(svc.ReservationStateError):
        svc.confirm_hold(r)


@pytest.mark.asyncio
async def test_first_mark_settles_and_releases_deposit():
    buyer = _buyer()
    listing = _listing(uuid.uuid4())
    r = svc.build_reservation(buyer=buyer, listing=listing)
    r.yk_payment_id = "pay-1"
    svc.confirm_hold(r)
    deps = _deps()
    now = datetime.now(UTC)
    await svc.mark_outcome(
        r, OutcomeParty.buyer, ReservationOutcome.sold, deps=deps, now=now
    )
    assert r.status == ReservationStatus.settling
    assert r.outcome == ReservationOutcome.sold
    assert r.outcome_set_by == OutcomeParty.buyer
    assert r.deposit_released_at is not None
    deps.yk.cancel_hold.assert_awaited_once_with(
        payment_id="pay-1", idempotence_key=f"{r.id}:release"
    )
    # listing untouched (stays reserved through settling)
    assert listing.status == ListingStatus.reserved


@pytest.mark.asyncio
async def test_correction_window_capped_by_hold_deadline():
    buyer = _buyer()
    listing = _listing(uuid.uuid4())
    r = svc.build_reservation(buyer=buyer, listing=listing)
    r.yk_payment_id = "pay-1"
    svc.confirm_hold(r)
    # now near hold deadline so cap applies
    now = r.hold_deadline - timedelta(hours=2)
    await svc.mark_outcome(
        r, OutcomeParty.buyer, ReservationOutcome.sold, deps=_deps(), now=now
    )
    assert r.correction_deadline == r.hold_deadline


@pytest.mark.asyncio
async def test_outcome_change_budget():
    buyer = _buyer()
    listing = _listing(uuid.uuid4())
    r = svc.build_reservation(buyer=buyer, listing=listing)
    r.yk_payment_id = "pay-1"
    svc.confirm_hold(r)
    deps = _deps()
    now = datetime.now(UTC)
    await svc.mark_outcome(
        r, OutcomeParty.buyer, ReservationOutcome.sold, deps=deps, now=now
    )

    # same value → no-op, no budget spent
    await svc.mark_outcome(
        r, OutcomeParty.buyer, ReservationOutcome.sold, deps=deps, now=now
    )
    assert r.buyer_change_used is False

    # seller changes once → applied
    await svc.mark_outcome(
        r, OutcomeParty.seller, ReservationOutcome.not_sold, deps=deps, now=now
    )
    assert r.outcome == ReservationOutcome.not_sold
    assert r.seller_change_used is True

    # seller changes again → locked
    with pytest.raises(svc.OutcomeLockedError):
        await svc.mark_outcome(
            r, OutcomeParty.seller, ReservationOutcome.sold, deps=deps, now=now
        )

    # buyer still has their one change
    await svc.mark_outcome(
        r, OutcomeParty.buyer, ReservationOutcome.sold, deps=deps, now=now
    )
    assert r.outcome == ReservationOutcome.sold
    assert r.buyer_change_used is True

    # only cancel_hold from the first mark
    deps.yk.cancel_hold.assert_awaited_once()


@pytest.mark.asyncio
async def test_outcome_window_closed():
    buyer = _buyer()
    listing = _listing(uuid.uuid4())
    r = svc.build_reservation(buyer=buyer, listing=listing)
    r.yk_payment_id = "pay-1"
    svc.confirm_hold(r)
    deps = _deps()
    start = datetime.now(UTC)
    await svc.mark_outcome(
        r, OutcomeParty.buyer, ReservationOutcome.sold, deps=deps, now=start
    )
    after = r.correction_deadline + timedelta(seconds=1)
    with pytest.raises(svc.OutcomeWindowClosedError):
        await svc.mark_outcome(
            r, OutcomeParty.seller, ReservationOutcome.not_sold, deps=deps, now=after
        )


def test_finalize_sets_listing_status():
    buyer = _buyer()
    listing = _listing(uuid.uuid4())
    r = svc.build_reservation(buyer=buyer, listing=listing)
    r.status = ReservationStatus.settling
    r.outcome = ReservationOutcome.sold
    svc.finalize(r, listing)
    assert r.status == ReservationStatus.completed
    assert listing.status == ListingStatus.sold

    listing2 = _listing(uuid.uuid4())
    r2 = svc.build_reservation(buyer=buyer, listing=listing2)
    r2.status = ReservationStatus.settling
    r2.outcome = ReservationOutcome.not_sold
    svc.finalize(r2, listing2)
    assert listing2.status == ListingStatus.active


@pytest.mark.asyncio
async def test_cancel_releases_and_frees_listing():
    buyer = _buyer()
    listing = _listing(uuid.uuid4())
    r = svc.build_reservation(buyer=buyer, listing=listing)
    r.yk_payment_id = "pay-1"
    svc.confirm_hold(r)
    deps = _deps()
    await svc.cancel(r, listing, reason=CancelReason.buyer_cancelled, deps=deps)
    assert r.status == ReservationStatus.cancelled
    assert r.cancel_reason == CancelReason.buyer_cancelled
    assert listing.status == ListingStatus.active
    deps.yk.cancel_hold.assert_awaited_once()

    # idempotent on terminal
    await svc.cancel(r, listing, reason=CancelReason.admin, deps=deps)
    deps.yk.cancel_hold.assert_awaited_once()
