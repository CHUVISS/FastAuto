from abc import ABC, abstractmethod


class SmsSendError(Exception):
    pass


class SmsRejectedError(SmsSendError):
    def __init__(self, reason: str, code: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.code = code


class SmsProviderUnavailableError(SmsSendError):
    pass


class SmsService(ABC):
    @abstractmethod
    async def send(self, phone: str, text: str) -> None: ...


def get_sms_service(backend: str | None = None) -> SmsService:
    from app.core.config import settings
    from app.services.sms.exolve_sms import ExolveSmsService
    from app.services.sms.fake_sms import FakeSmsService

    backend = backend or settings.SMS_BACKEND
    if backend == "exolve":
        return ExolveSmsService(
            api_key=settings.EXOLVE_API_KEY,
            from_number=settings.EXOLVE_FROM_NUMBER,
            base_url=settings.EXOLVE_BASE_URL,
        )
    return FakeSmsService()
