from unittest.mock import MagicMock, patch

import pytest

from app.services.payments import yookassa_service as yk

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_create_hold_sends_capture_false_and_no_deal():
    fake = MagicMock(id="pay_1", confirmation=MagicMock(confirmation_url="https://pay"))
    with patch.object(yk.Payment, "create", return_value=fake) as m:
        res = await yk.create_hold(
            amount_rub=5000,
            description="Депозит за бронь",
            idempotence_key="r1:hold",
        )
    payload = m.call_args.args[0]
    assert payload["capture"] is False
    assert payload["amount"] == {"value": "5000.00", "currency": "RUB"}
    assert "deal" not in payload
    assert res.id == "pay_1"
    assert res.confirmation_url == "https://pay"


@pytest.mark.asyncio
async def test_cancel_hold_calls_payment_cancel():
    with patch.object(
        yk.Payment, "cancel", return_value=MagicMock(status="canceled")
    ) as m:
        status = await yk.cancel_hold(payment_id="pay_1", idempotence_key="r1:release")
    m.assert_called_once_with("pay_1", "r1:release")
    assert status == "canceled"
