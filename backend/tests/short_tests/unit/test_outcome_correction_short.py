from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models.listings import Condition, Listing, ListingStatus
from app.models.reservations import OutcomeParty, ReservationOutcome
from app.services.reservations import reservation_service as svc

pytestmark = pytest.mark.unit


def _setup_settling():
    listing = Listing(
        id=uuid.uuid4(),
        seller_id=uuid.uuid4(),
        modification_id="M1",
        mark_id="BMW",
        model_id="BMW_5",
        year=2019,
        price=2_500_000,
        mileage=1,
        color_id="black",
        condition=Condition.good,
        city_id="7700000000000",
        status=ListingStatus.active,
    )
    from app.models.users import User

    buyer = User(
        id=uuid.uuid4(),
        full_name="B",
        email=f"b{uuid.uuid4().hex[:8]}@e.com",
        hashed_password="x",
        phone_verified=True,
    )
    r = svc.build_reservation(buyer=buyer, listing=listing)
    r.yk_payment_id = "pay-1"
    svc.confirm_hold(r)
    deps = SimpleNamespace(yk=SimpleNamespace(cancel_hold=AsyncMock(return_value="ok")))
    return r, listing, deps


@pytest.mark.asyncio
async def test_same_outcome_value_is_noop_and_does_not_spend_budget():
    r, _, deps = _setup_settling()
    await svc.mark_outcome(r, OutcomeParty.buyer, ReservationOutcome.sold, deps=deps)
    await svc.mark_outcome(r, OutcomeParty.buyer, ReservationOutcome.sold, deps=deps)

    assert r.buyer_change_used is False
    deps.yk.cancel_hold.assert_awaited_once()


@pytest.mark.asyncio
async def test_party_second_change_after_initial_is_locked():
    r, _, deps = _setup_settling()
    now = datetime.now(UTC)
    await svc.mark_outcome(
        r, OutcomeParty.buyer, ReservationOutcome.sold, deps=deps, now=now
    )
    await svc.mark_outcome(
        r,
        OutcomeParty.buyer,
        ReservationOutcome.not_sold,
        deps=deps,
        now=now + timedelta(minutes=1),
    )

    with pytest.raises(svc.OutcomeLockedError):
        await svc.mark_outcome(
            r,
            OutcomeParty.buyer,
            ReservationOutcome.sold,
            deps=deps,
            now=now + timedelta(minutes=2),
        )
