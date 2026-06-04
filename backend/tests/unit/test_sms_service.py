import json

import httpx
import pytest

from app.services.sms.exolve_sms import ExolveSmsService
from app.services.sms.fake_sms import FakeSmsService
from app.services.sms.sms_service import (
    SmsProviderUnavailableError,
    SmsRejectedError,
    SmsSendError,
    get_sms_service,
)

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_fake_records_messages():
    sms = FakeSmsService()
    await sms.send("79161234567", "Код: 123456")
    assert sms.sent == [("79161234567", "Код: 123456")]


@pytest.mark.asyncio
async def test_exolve_builds_correct_request():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        captured["json"] = json.loads(request.content)
        return httpx.Response(200, json={"message_id": "1"})

    sms = ExolveSmsService(
        api_key="KEY",
        from_number="79990000000",
        base_url="https://api.exolve.ru",
        transport=httpx.MockTransport(handler),
    )
    await sms.send("79161234567", "Код: 123456")

    assert captured["url"].endswith("/messaging/v1/SendSMS")
    assert captured["auth"] == "Bearer KEY"
    assert captured["json"] == {
        "number": "79990000000",
        "destination": "79161234567",
        "text": "Код: 123456",
    }


@pytest.mark.asyncio
async def test_exolve_raises_provider_unavailable_on_5xx():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    sms = ExolveSmsService(
        api_key="KEY",
        from_number="79990000000",
        base_url="https://api.exolve.ru",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(SmsProviderUnavailableError):
        await sms.send("79161234567", "x")


@pytest.mark.asyncio
async def test_exolve_raises_rejected_on_user_400():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"message": "destination is not permitted for delivery"}},
        )

    sms = ExolveSmsService(
        api_key="KEY",
        from_number="79990000000",
        base_url="https://api.exolve.ru",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(SmsRejectedError):
        await sms.send("70000000000", "x")


@pytest.mark.asyncio
async def test_exolve_raises_provider_unavailable_on_provider_400():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400, json={"error": {"message": "alpha name is not active"}}
        )

    sms = ExolveSmsService(
        api_key="KEY",
        from_number="79990000000",
        base_url="https://api.exolve.ru",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(SmsProviderUnavailableError):
        await sms.send("79161234567", "x")


@pytest.mark.asyncio
async def test_exolve_raises_provider_unavailable_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "authorization token is invalid"})

    sms = ExolveSmsService(
        api_key="BAD",
        from_number="79990000000",
        base_url="https://api.exolve.ru",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(SmsProviderUnavailableError):
        await sms.send("79161234567", "x")


def test_rejected_and_unavailable_inherit_sms_send_error():
    assert issubclass(SmsRejectedError, SmsSendError)
    assert issubclass(SmsProviderUnavailableError, SmsSendError)


def test_factory_returns_fake_for_fake_backend():
    assert isinstance(get_sms_service("fake"), FakeSmsService)
