import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_webhook_valid_ip_processes_then_dedupes(committed_client: AsyncClient):
    oid = f"pay-{uuid.uuid4().hex[:8]}"
    event = {"event": "payment.waiting_for_capture", "object": {"id": oid}}
    with (
        patch("app.services.payments.webhook.is_yookassa_ip", return_value=True),
        patch("app.api.routes.webhooks.build_handlers") as bh,
    ):
        bh.return_value = AsyncMock()
        first = await committed_client.post("/api/v1/webhooks/yookassa", json=event)
        second = await committed_client.post("/api/v1/webhooks/yookassa", json=event)
        bh.return_value.on_hold_confirmed.assert_awaited_once_with(oid)
    assert first.status_code == 200
    assert first.json()["processed"] is True
    assert second.status_code == 200
    assert second.json()["processed"] is False


@pytest.mark.asyncio
async def test_webhook_rejects_unknown_ip(committed_client: AsyncClient):
    with patch("app.services.payments.webhook.is_yookassa_ip", return_value=False):
        resp = await committed_client.post(
            "/api/v1/webhooks/yookassa",
            json={"event": "payment.succeeded", "object": {"id": "x"}},
        )
    assert resp.status_code == 403
