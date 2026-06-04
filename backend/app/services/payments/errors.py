import requests
from yookassa.domain.exceptions import (
    ApiError,
    BadRequestError,
    ForbiddenError,
    GoneError,
    NotFoundError,
    UnauthorizedError,
)

type YkRawError = ApiError | requests.exceptions.RequestException
YK_RAW_ERRORS: tuple[type[BaseException], ...] = (
    ApiError,
    requests.exceptions.RequestException,
)


class PaymentProviderError(Exception): ...


class HoldCreationError(PaymentProviderError): ...


class PaymentLookupError(PaymentProviderError): ...


class DepositReleaseError(PaymentProviderError): ...


class DepositReleaseTransientError(DepositReleaseError): ...


class DepositReleaseTerminalError(DepositReleaseError): ...


_TERMINAL_API_ERRORS = (
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    GoneError,
)


def to_release_error(exc: YkRawError) -> DepositReleaseError:
    if isinstance(exc, _TERMINAL_API_ERRORS):
        return DepositReleaseTerminalError(str(exc))
    return DepositReleaseTransientError(str(exc))
