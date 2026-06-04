import fakeredis.aioredis
import pytest

from app.services.payments import webhook
from app.services.payments.errors import PaymentLookupError

pytestmark = pytest.mark.unit


def _event():
    return {"event": "payment.waiting_for_capture", "object": {"id": "pay_1"}}


class _OkHandlers:
    def __init__(self):
        self.calls = 0

    async def on_hold_confirmed(self, payment_id):
        self.calls += 1

    async def on_hold_released(self, payment_id):
        return None


class _FailingHandlers:
    async def on_hold_confirmed(self, payment_id):
        raise PaymentLookupError(payment_id)

    async def on_hold_released(self, payment_id):
        return None


async def test_success_keeps_dedup_key():
    redis = fakeredis.aioredis.FakeRedis()
    handlers = _OkHandlers()
    assert await webhook.handle_event(_event(), redis=redis, handlers=handlers) is True
    assert await webhook.handle_event(_event(), redis=redis, handlers=handlers) is False
    assert handlers.calls == 1


async def test_handler_failure_releases_key_and_allows_redelivery():
    redis = fakeredis.aioredis.FakeRedis()
    with pytest.raises(PaymentLookupError):
        await webhook.handle_event(_event(), redis=redis, handlers=_FailingHandlers())
    retry = _OkHandlers()
    assert await webhook.handle_event(_event(), redis=redis, handlers=retry) is True
    assert retry.calls == 1
