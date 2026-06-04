import logging

import httpx

from app.services.sms.sms_service import (
    SmsProviderUnavailableError,
    SmsRejectedError,
    SmsService,
)

logger = logging.getLogger(__name__)

_USER_REJECTION_HINTS = (
    "destination is not permitted",
    "exceeded the limit of segments",
    "text does not match the template",
    "cannot send template sms not with an alpha name",
    "invalid value",
    "syntax error",
    "unknown field",
)


def _classify_400(body_text: str) -> bool:
    body_lower = body_text.lower()
    return any(hint in body_lower for hint in _USER_REJECTION_HINTS)


class ExolveSmsService(SmsService):
    def __init__(
        self,
        api_key: str,
        from_number: str,
        base_url: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._from = from_number
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    async def send(self, phone: str, text: str) -> None:
        try:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=10
            ) as client:
                resp = await client.post(
                    f"{self._base_url}/messaging/v1/SendSMS",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={
                        "number": self._from,
                        "destination": phone,
                        "text": text,
                    },
                )
                resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            body = e.response.text
            logger.exception(
                "Exolve SMS send failed for %s: status=%s body=%s",
                phone,
                status,
                body,
            )
            if status == 400 and _classify_400(body):
                raise SmsRejectedError(
                    "destination not supported by provider", code=str(status)
                ) from e
            raise SmsProviderUnavailableError(f"provider returned {status}") from e
        except httpx.HTTPError as e:
            logger.exception("Exolve SMS request failed for %s", phone)
            raise SmsProviderUnavailableError("provider unreachable") from e
