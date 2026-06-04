from unittest.mock import MagicMock, patch

import pytest

from app.services.payments import safe_deal as yk

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_create_deal_uses_deal_closed():
    fake = MagicMock(id="dl-123")
    with patch.object(yk.Deal, "create", return_value=fake) as create:
        deal_id = await yk.create_deal(idempotence_key="tx:deal")
    assert deal_id == "dl-123"
    payload, key = create.call_args.args
    assert payload == {"type": "safe_deal", "fee_moment": "deal_closed"}
    assert key == "tx:deal"


@pytest.mark.asyncio
async def test_create_payment_includes_settlements():
    fake = MagicMock(id="pay-1", confirmation=MagicMock(confirmation_url="https://pay"))
    with patch.object(yk.Payment, "create", return_value=fake) as create:
        res = await yk.create_payment(
            amount_rub=2_500_000,
            deal_id="dl-123",
            seller_payout_rub=2_450_000,
            description="Auto",
            idempotence_key="tx:payment",
        )
    payload = create.call_args.args[0]
    assert payload["amount"] == {"value": "2500000.00", "currency": "RUB"}
    assert payload["capture"] is True
    assert payload["deal"]["id"] == "dl-123"
    assert payload["deal"]["settlements"] == [
        {"type": "payout", "amount": {"value": "2450000.00", "currency": "RUB"}}
    ]
    assert res.confirmation_url == "https://pay"


@pytest.mark.asyncio
async def test_create_payout_uses_token_and_metadata():
    with patch.object(yk.Payout, "create", return_value=MagicMock(id="po-1")) as create:
        pid = await yk.create_payout(
            amount_rub=2_450_000,
            deal_id="dl-123",
            payout_token="tok_abc",
            metadata={"transaction_id": "tx-1"},
            idempotence_key="tx-1:payout",
        )
    payload = create.call_args.args[0]
    assert payload["amount"] == {"value": "2450000.00", "currency": "RUB"}
    assert payload["deal"] == {"id": "dl-123"}
    assert payload["payout_token"] == "tok_abc"
    assert payload["metadata"] == {"transaction_id": "tx-1"}
    assert "payout_destination_data" not in payload
    assert pid == "po-1"


@pytest.mark.asyncio
async def test_create_refund_includes_refund_settlements():
    with patch.object(yk.Refund, "create", return_value=MagicMock(id="re-1")) as create:
        await yk.create_refund(
            payment_id="pay-1",
            amount_rub=2_500_000,
            seller_payout_rub=2_450_000,
            idempotence_key="tx:refund",
        )
    payload = create.call_args.args[0]
    assert payload["payment_id"] == "pay-1"
    assert payload["deal"]["refund_settlements"] == [
        {"type": "payout", "amount": {"value": "2450000.00", "currency": "RUB"}}
    ]
