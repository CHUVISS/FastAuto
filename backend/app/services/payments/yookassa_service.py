import asyncio
from typing import Any

from yookassa import Configuration, Payment

from app.core.config import settings
from app.services.payments.errors import (
    YK_RAW_ERRORS,
    HoldCreationError,
    PaymentLookupError,
    to_release_error,
)

# Shared helpers + dormant Safe Deal functions live in ``safe_deal``
# re-exported here for the legacy transaction/admin/scheduler callers
from app.services.payments.safe_deal import (
    CreatedPayment,
    _money,
    create_deal,
    create_payment,
    create_payout,
    create_refund,
    find_payouts_by_metadata,
)

Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

__all__ = [
    "CreatedPayment",
    "cancel_hold",
    "create_deal",
    "create_hold",
    "create_payment",
    "create_payout",
    "create_refund",
    "find_payment",
    "find_payouts_by_metadata",
]


def _fake_mode() -> bool:
    return settings.PAYMENT_BACKEND == "fake" or not settings.YOOKASSA_SHOP_ID


class _FakePayment:
    """Mock payment object returned in fake mode."""
    def __init__(self, payment_id: str) -> None:
        self.id = payment_id
        self.status = "waiting_for_capture"
        self.confirmation = None


async def create_hold(
    *,
    amount_rub: int,
    description: str,
    idempotence_key: str,
    return_url: str | None = None,
) -> CreatedPayment:
    if _fake_mode():
        # reservation_id is the part before ":" in the idempotence_key
        reservation_id = idempotence_key.split(":")[0]
        fake_id = f"fake_{reservation_id}"
        base = settings.BACKEND_PUBLIC_URL.rstrip("/")
        confirm_url = f"{base}/api/v1/payments/fake-confirm?reservation_id={reservation_id}"
        return CreatedPayment(id=fake_id, confirmation_url=confirm_url)

    payload = {
        "amount": _money(amount_rub),
        "capture": False,
        "confirmation": {
            "type": "redirect",
            "return_url": return_url or settings.YOOKASSA_RETURN_URL,
        },
        "description": description,
    }
    try:
        payment = await asyncio.to_thread(Payment.create, payload, idempotence_key)
    except YK_RAW_ERRORS as exc:
        raise HoldCreationError(str(exc)) from exc
    url = getattr(getattr(payment, "confirmation", None), "confirmation_url", None)
    return CreatedPayment(id=str(payment.id), confirmation_url=url)


async def cancel_hold(*, payment_id: str, idempotence_key: str) -> str:
    if _fake_mode():
        return "canceled"
    try:
        res = await asyncio.to_thread(Payment.cancel, payment_id, idempotence_key)
    except YK_RAW_ERRORS as exc:
        raise to_release_error(exc) from exc
    return str(getattr(res, "status", "canceled"))


async def find_payment(payment_id: str) -> Any:
    if _fake_mode():
        return _FakePayment(payment_id)
    try:
        return await asyncio.to_thread(Payment.find_one, payment_id)
    except YK_RAW_ERRORS as exc:
        raise PaymentLookupError(str(payment_id)) from exc
