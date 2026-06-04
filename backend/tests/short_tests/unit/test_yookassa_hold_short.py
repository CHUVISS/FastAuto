from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.payments import yookassa_service as yk

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_create_hold_uses_capture_false_and_omits_deal():
    fake = MagicMock(id="pay_1", confirmation=MagicMock(confirmation_url="https://pay"))
    with patch.object(yk.Payment, "create", return_value=fake) as m:
        result = await yk.create_hold(
            amount_rub=5000, description="Депозит", idempotence_key="r1:hold"
        )

    payload = m.call_args.args[0]
    assert payload["capture"] is False
    assert "deal" not in payload
    assert result.id == "pay_1"
