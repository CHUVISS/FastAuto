import logging
from typing import Any, Protocol

from redis.asyncio import Redis
from yookassa.domain.common import SecurityHelper

from app.services.payments.errors import PaymentLookupError

logger = logging.getLogger(__name__)

_EVENT_TTL = 7 * 24 * 3600


class TransactionHandlers(Protocol):
    async def on_hold_confirmed(self, payment_id: str) -> None: ...
    async def on_hold_released(self, payment_id: str) -> None: ...


def is_yookassa_ip(ip: str) -> bool:
    return bool(SecurityHelper().is_ip_trusted(ip))


_DISPATCH = {
    "payment.waiting_for_capture": "on_hold_confirmed",
    "payment.canceled": "on_hold_released",
}


async def handle_event(
    event: dict[str, Any], *, redis: Redis, handlers: TransactionHandlers
) -> bool:
    name = event["event"]
    object_id = event["object"]["id"]
    log_ctx = {"yk_event": name, "object_id": object_id}
    if not await redis.set(f"yk_event:{object_id}:{name}", "1", ex=_EVENT_TTL, nx=True):
        logger.info("yk webhook duplicate, dedup", extra=log_ctx)
        return False
    method = _DISPATCH.get(name)
    if method is None:
        logger.warning("yk webhook unknown event, accepted but ignored", extra=log_ctx)
        return True
    logger.info("yk webhook dispatch", extra=log_ctx)
    try:
        await getattr(handlers, method)(object_id)
    except PaymentLookupError:
        await redis.delete(f"yk_event:{object_id}:{name}")
        raise
    return True
