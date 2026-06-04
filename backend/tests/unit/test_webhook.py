from unittest.mock import AsyncMock, patch

import pytest
from fakeredis.aioredis import FakeRedis

from app.services.payments import webhook

pytestmark = pytest.mark.unit


def test_ip_allowlist_uses_sdk_security_helper():
    with patch.object(webhook, "SecurityHelper") as sh:
        sh.return_value.is_ip_trusted.side_effect = lambda ip: ip == "185.71.76.1"
        assert webhook.is_yookassa_ip("185.71.76.1") is True
        assert webhook.is_yookassa_ip("8.8.8.8") is False


@pytest.mark.asyncio
async def test_duplicate_event_is_noop():
    redis = FakeRedis()
    handlers = AsyncMock()
    event = {"event": "payment.waiting_for_capture", "object": {"id": "pay-1"}}
    first = await webhook.handle_event(event, redis=redis, handlers=handlers)
    second = await webhook.handle_event(event, redis=redis, handlers=handlers)
    assert first is True
    assert second is False
    handlers.on_hold_confirmed.assert_awaited_once_with("pay-1")


@pytest.mark.asyncio
async def test_dispatch_routes_hold_events():
    redis = FakeRedis()
    handlers = AsyncMock()
    for name, oid in [
        ("payment.waiting_for_capture", "pay-1"),
        ("payment.canceled", "pay-9"),
    ]:
        await webhook.handle_event(
            {"event": name, "object": {"id": oid}}, redis=redis, handlers=handlers
        )
    handlers.on_hold_confirmed.assert_awaited_once_with("pay-1")
    handlers.on_hold_released.assert_awaited_once_with("pay-9")


@pytest.mark.asyncio
async def test_unknown_event_accepted_but_ignored():
    redis = FakeRedis()
    handlers = AsyncMock()
    processed = await webhook.handle_event(
        {"event": "payout.succeeded", "object": {"id": "po-1"}},
        redis=redis,
        handlers=handlers,
    )
    assert processed is True
    handlers.on_hold_confirmed.assert_not_awaited()
