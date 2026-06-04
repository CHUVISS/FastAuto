import logging

from app.services.sms.sms_service import SmsService

logger = logging.getLogger(__name__)


class FakeSmsService(SmsService):
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send(self, phone: str, text: str) -> None:
        self.sent.append((phone, text))
        logger.info("FakeSMS to %s: %s", phone, text)
