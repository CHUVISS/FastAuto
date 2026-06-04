import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import fakeredis.aioredis
import pytest

from app.api.routes.payments import _resolve_status
from app.models.reservations import Reservation, ReservationStatus
from app.schemas.payments import ReturnStatus
from app.services.payments.errors import PaymentLookupError

pytestmark = pytest.mark.unit


def _res(status, yk_payment_id="pay_1"):
    return Reservation(
        id=uuid.uuid4(),
        listing_id=uuid.uuid4(),
        buyer_id=uuid.uuid4(),
        seller_id=uuid.uuid4(),
        deposit_amount=5000,
        yk_payment_id=yk_payment_id,
        status=status,
        payment_deadline=datetime.now(UTC) + timedelta(minutes=30),
        hold_deadline=datetime.now(UTC) + timedelta(days=5),
    )


async def test_active_returns_ok():
    r = _res(ReservationStatus.active)
    redis = fakeredis.aioredis.FakeRedis()
    assert await _resolve_status(r, redis) == ReturnStatus.ok


async def test_cancelled_returns_cancelled():
    r = _res(ReservationStatus.cancelled)
    redis = fakeredis.aioredis.FakeRedis()
    assert await _resolve_status(r, redis) == ReturnStatus.cancelled


async def test_settling_returns_failed():
    r = _res(ReservationStatus.settling)
    redis = fakeredis.aioredis.FakeRedis()
    assert await _resolve_status(r, redis) == ReturnStatus.failed


async def test_pending_payment_no_yk_id_returns_pending():
    r = _res(ReservationStatus.pending_payment, yk_payment_id=None)
    redis = fakeredis.aioredis.FakeRedis()
    assert await _resolve_status(r, redis) == ReturnStatus.pending


async def test_pending_with_waiting_for_capture_returns_ok(monkeypatch):
    r = _res(ReservationStatus.pending_payment)
    redis = fakeredis.aioredis.FakeRedis()
    from app.api.routes import payments as route_mod

    async def _find(_pid):
        return SimpleNamespace(status="waiting_for_capture")

    monkeypatch.setattr(route_mod.yk, "find_payment", _find)
    monkeypatch.setattr(
        route_mod,
        "build_handlers",
        lambda _sf, _r: SimpleNamespace(on_hold_confirmed=AsyncMock()),
    )
    assert await _resolve_status(r, redis) == ReturnStatus.ok


async def test_pending_with_yk_pending_returns_pending(monkeypatch):
    r = _res(ReservationStatus.pending_payment)
    redis = fakeredis.aioredis.FakeRedis()
    from app.api.routes import payments as route_mod

    async def _find(_pid):
        return SimpleNamespace(status="pending")

    monkeypatch.setattr(route_mod.yk, "find_payment", _find)
    assert await _resolve_status(r, redis) == ReturnStatus.pending


async def test_pending_lookup_failure_degrades_to_pending(monkeypatch):
    r = _res(ReservationStatus.pending_payment)
    redis = fakeredis.aioredis.FakeRedis()
    from app.api.routes import payments as route_mod

    async def _find(_pid):
        raise PaymentLookupError(_pid)

    monkeypatch.setattr(route_mod.yk, "find_payment", _find)
    assert await _resolve_status(r, redis) == ReturnStatus.pending
