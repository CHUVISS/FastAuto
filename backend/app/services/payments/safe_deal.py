import asyncio
from dataclasses import dataclass
from typing import Any

from yookassa import Configuration, Deal, Payment, Payout, Refund

from app.core.config import settings

Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


def _money(rub: int) -> dict[str, str]:
    return {"value": f"{rub:.2f}", "currency": "RUB"}


@dataclass
class CreatedPayment:
    id: str
    confirmation_url: str | None


def _payout_settlement(seller_payout_rub: int) -> list[dict[str, Any]]:
    return [{"type": "payout", "amount": _money(seller_payout_rub)}]


async def create_deal(*, idempotence_key: str) -> str:
    payload = {"type": "safe_deal", "fee_moment": "deal_closed"}
    deal = await asyncio.to_thread(Deal.create, payload, idempotence_key)
    return str(deal.id)


async def create_payment(
    *,
    amount_rub: int,
    deal_id: str,
    seller_payout_rub: int,
    description: str,
    idempotence_key: str,
    capture: bool = True,
) -> CreatedPayment:
    payload = {
        "amount": _money(amount_rub),
        "capture": capture,
        "confirmation": {
            "type": "redirect",
            "return_url": settings.YOOKASSA_RETURN_URL,
        },
        "description": description,
        "deal": {"id": deal_id, "settlements": _payout_settlement(seller_payout_rub)},
    }
    payment = await asyncio.to_thread(Payment.create, payload, idempotence_key)
    url = getattr(getattr(payment, "confirmation", None), "confirmation_url", None)
    return CreatedPayment(id=str(payment.id), confirmation_url=url)


async def create_payout(
    *,
    amount_rub: int,
    deal_id: str,
    payout_token: str,
    metadata: dict[str, Any],
    idempotence_key: str,
) -> str:
    payload = {
        "amount": _money(amount_rub),
        "payout_token": payout_token,
        "deal": {"id": deal_id},
        "metadata": metadata,
        "description": "Выплата продавцу по сделке",
    }
    payout = await asyncio.to_thread(Payout.create, payload, idempotence_key)
    return str(payout.id)


async def find_payouts_by_metadata(metadata: dict[str, Any]) -> list[Any]:
    params = {f"metadata.{k}": v for k, v in metadata.items()}
    res = await asyncio.to_thread(Payout.list, params)
    return list(getattr(res, "items", []) or [])


async def create_refund(
    *,
    payment_id: str,
    amount_rub: int,
    seller_payout_rub: int,
    idempotence_key: str,
) -> str:
    payload = {
        "payment_id": payment_id,
        "amount": _money(amount_rub),
        "deal": {"refund_settlements": _payout_settlement(seller_payout_rub)},
    }
    refund = await asyncio.to_thread(Refund.create, payload, idempotence_key)
    return str(refund.id)
