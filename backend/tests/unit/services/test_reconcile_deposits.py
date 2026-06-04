import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest

from app.models.reservations import Reservation, ReservationStatus
from app.services import scheduler as sched
from app.services.payments.errors import (
    DepositReleaseTerminalError,
    DepositReleaseTransientError,
)
from app.services.reservations.reservation_service import ReservationDeps
from app.services.sms.fake_sms import FakeSmsService

pytestmark = pytest.mark.unit


class _FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def commit(self):
        return None


def _factory():
    return _FakeSession()


@dataclass
class _FakeYk:
    side_effect: BaseException | None = None
    calls: list[str] = field(default_factory=list)

    async def cancel_hold(self, *, payment_id: str, idempotence_key: str) -> str:
        self.calls.append(payment_id)
        if self.side_effect is not None:
            raise self.side_effect
        return "canceled"


def _res(released=None, hold_offset_days=5):
    return Reservation(
        id=uuid.uuid4(),
        listing_id=uuid.uuid4(),
        buyer_id=uuid.uuid4(),
        seller_id=uuid.uuid4(),
        deposit_amount=5000,
        yk_payment_id="pay_1",
        status=ReservationStatus.cancelled,
        deposit_released_at=released,
        payment_deadline=datetime.now(UTC),
        hold_deadline=datetime.now(UTC) + timedelta(days=hold_offset_days),
    )


async def _run(monkeypatch, reservations, side_effect=None) -> _FakeYk:
    fake = _FakeYk(side_effect=side_effect)
    monkeypatch.setattr(
        sched.res_svc,
        "default_deps",
        lambda: ReservationDeps(yk=fake, sms=FakeSmsService()),
    )

    async def _list(_session, _now):
        return reservations

    monkeypatch.setattr(sched.res_crud, "list_release_pending", _list)
    await sched.run_reconcile_deposits(session_factory=_factory)
    return fake


async def test_success_marks_released(monkeypatch):
    r = _res()
    await _run(monkeypatch, [r])
    assert r.deposit_released_at is not None


async def test_terminal_marks_released(monkeypatch):
    r = _res()
    fake = await _run(monkeypatch, [r], side_effect=DepositReleaseTerminalError("gone"))
    assert r.deposit_released_at is not None
    assert fake.calls == ["pay_1"]


async def test_transient_keeps_pending(monkeypatch):
    r = _res()
    await _run(monkeypatch, [r], side_effect=DepositReleaseTransientError("net"))
    assert r.deposit_released_at is None


async def test_past_grace_releases_without_yk_call(monkeypatch):
    r = _res(hold_offset_days=-2)
    fake = await _run(monkeypatch, [r], side_effect=DepositReleaseTerminalError("x"))
    assert r.deposit_released_at is not None
    assert fake.calls == []
