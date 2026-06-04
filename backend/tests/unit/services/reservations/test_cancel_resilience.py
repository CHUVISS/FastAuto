import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest

from app.models.listings import ListingStatus
from app.models.reservations import CancelReason, Reservation, ReservationStatus
from app.services.payments.errors import (
    DepositReleaseTerminalError,
    DepositReleaseTransientError,
)
from app.services.reservations import reservation_service as svc
from app.services.reservations.reservation_service import ReservationDeps
from app.services.sms.fake_sms import FakeSmsService

pytestmark = pytest.mark.unit


@dataclass
class _Listing:
    status: ListingStatus = ListingStatus.reserved


@dataclass
class _FakeYk:
    side_effect: BaseException | None = None
    calls: list[str] = field(default_factory=list)

    async def cancel_hold(self, *, payment_id: str, idempotence_key: str) -> str:
        self.calls.append(payment_id)
        if self.side_effect is not None:
            raise self.side_effect
        return "canceled"


def _res(status, **kw):
    return Reservation(
        id=uuid.uuid4(),
        listing_id=uuid.uuid4(),
        buyer_id=uuid.uuid4(),
        seller_id=uuid.uuid4(),
        deposit_amount=5000,
        yk_payment_id="pay_1",
        status=status,
        payment_deadline=datetime.now(UTC) + timedelta(hours=1),
        hold_deadline=datetime.now(UTC) + timedelta(days=5),
        **kw,
    )


def _deps(side_effect=None) -> ReservationDeps:
    return ReservationDeps(yk=_FakeYk(side_effect=side_effect), sms=FakeSmsService())


async def test_pending_payment_terminal_frees_listing_and_marks_released():
    r, lst = _res(ReservationStatus.pending_payment), _Listing()
    await svc.cancel(
        r,
        lst,
        reason=CancelReason.payment_abandoned,
        deps=_deps(DepositReleaseTerminalError("payment doesn't exist")),
    )
    assert lst.status == ListingStatus.active
    assert r.status == ReservationStatus.cancelled
    assert r.deposit_released_at is not None


async def test_active_terminal_frees_listing_but_keeps_release_pending():
    r, lst = _res(ReservationStatus.active), _Listing()
    await svc.cancel(
        r,
        lst,
        reason=CancelReason.buyer_cancelled,
        deps=_deps(DepositReleaseTerminalError("payment doesn't exist")),
    )
    assert lst.status == ListingStatus.active
    assert r.status == ReservationStatus.cancelled
    assert r.deposit_released_at is None


async def test_transient_frees_listing_and_defers_release():
    r, lst = _res(ReservationStatus.active), _Listing()
    await svc.cancel(
        r,
        lst,
        reason=CancelReason.buyer_cancelled,
        deps=_deps(DepositReleaseTransientError("connection reset")),
    )
    assert lst.status == ListingStatus.active
    assert r.deposit_released_at is None


async def test_success_marks_released():
    r, lst = _res(ReservationStatus.active), _Listing()
    await svc.cancel(r, lst, reason=CancelReason.buyer_cancelled, deps=_deps())
    assert lst.status == ListingStatus.active
    assert r.deposit_released_at is not None


async def test_already_released_short_circuits():
    r, lst = _res(ReservationStatus.active), _Listing()
    r.deposit_released_at = datetime.now(UTC)
    yk = _FakeYk()
    deps = ReservationDeps(yk=yk, sms=FakeSmsService())
    await svc.cancel(
        r,
        lst,
        reason=CancelReason.hold_released_externally,
        deps=deps,
    )
    assert lst.status == ListingStatus.active
    assert r.status == ReservationStatus.cancelled
    assert yk.calls == []


async def test_release_defers_when_due_in_future():
    r = _res(ReservationStatus.cancelled)
    r.deposit_release_due_at = datetime.now(UTC) + timedelta(hours=1)
    yk = _FakeYk()
    deps = ReservationDeps(yk=yk, sms=FakeSmsService())
    await svc._release_deposit(r, deps=deps)
    assert yk.calls == []
    assert r.deposit_released_at is None


async def test_release_proceeds_when_due_in_past():
    r = _res(ReservationStatus.cancelled)
    r.deposit_release_due_at = datetime.now(UTC) - timedelta(seconds=1)
    yk = _FakeYk()
    deps = ReservationDeps(yk=yk, sms=FakeSmsService())
    await svc._release_deposit(r, deps=deps)
    assert yk.calls == ["pay_1"]
    assert r.deposit_released_at is not None


async def test_cancel_with_future_due_skips_release_but_frees_listing():
    r, lst = _res(ReservationStatus.active), _Listing()
    r.deposit_release_due_at = datetime.now(UTC) + timedelta(hours=6)
    yk = _FakeYk()
    deps = ReservationDeps(yk=yk, sms=FakeSmsService())
    await svc.cancel(r, lst, reason=CancelReason.buyer_cancelled, deps=deps)
    assert lst.status == ListingStatus.active
    assert r.status == ReservationStatus.cancelled
    assert yk.calls == []
    assert r.deposit_released_at is None
