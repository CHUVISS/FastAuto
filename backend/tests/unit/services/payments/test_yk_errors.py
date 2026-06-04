import pytest
import requests
from yookassa.domain.exceptions import (
    BadRequestError,
    ForbiddenError,
    GoneError,
    InternalServerError,
    NotFoundError,
    TooManyRequestsError,
    UnauthorizedError,
)

from app.services.payments import yookassa_service as yk
from app.services.payments.errors import (
    DepositReleaseTerminalError,
    DepositReleaseTransientError,
    HoldCreationError,
    PaymentLookupError,
    to_release_error,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "exc",
    [
        BadRequestError({"code": "invalid_request"}),
        NotFoundError({}),
        ForbiddenError({}),
        GoneError({}),
        UnauthorizedError({}),
    ],
)
def test_terminal_mapping(exc):
    assert isinstance(to_release_error(exc), DepositReleaseTerminalError)


@pytest.mark.parametrize(
    "exc",
    [
        requests.exceptions.ConnectionError(),
        requests.exceptions.Timeout(),
        InternalServerError({}),
        TooManyRequestsError({}),
    ],
)
def test_transient_mapping(exc):
    assert isinstance(to_release_error(exc), DepositReleaseTransientError)


async def test_cancel_hold_raises_terminal(monkeypatch):
    def _raise(*_a, **_k):
        raise BadRequestError({"code": "invalid_request"})

    monkeypatch.setattr(yk.Payment, "cancel", _raise)
    with pytest.raises(DepositReleaseTerminalError):
        await yk.cancel_hold(payment_id="p1", idempotence_key="p1:release")


async def test_cancel_hold_raises_transient(monkeypatch):
    def _raise(*_a, **_k):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(yk.Payment, "cancel", _raise)
    with pytest.raises(DepositReleaseTransientError):
        await yk.cancel_hold(payment_id="p1", idempotence_key="p1:release")


async def test_create_hold_raises_hold_creation_error(monkeypatch):
    def _raise(*_a, **_k):
        raise InternalServerError({})

    monkeypatch.setattr(yk.Payment, "create", _raise)
    with pytest.raises(HoldCreationError):
        await yk.create_hold(
            amount_rub=5000, description="d", idempotence_key="r1:hold"
        )


async def test_find_payment_raises_lookup_error(monkeypatch):
    def _raise(*_a, **_k):
        raise NotFoundError({})

    monkeypatch.setattr(yk.Payment, "find_one", _raise)
    with pytest.raises(PaymentLookupError):
        await yk.find_payment("p1")
