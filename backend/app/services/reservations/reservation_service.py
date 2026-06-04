import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from redis.asyncio import Redis

from app.core.config import settings
from app.crud import listings as listing_crud
from app.crud import reservations as res_crud
from app.crud import viewings as viewings_crud
from app.models.listings import Listing, ListingStatus
from app.models.reservations import (
    CancelReason,
    OutcomeParty,
    Reservation,
    ReservationOutcome,
    ReservationStatus,
)
from app.models.users import User
from app.services.payments import yookassa_service as yk
from app.services.payments.errors import (
    DepositReleaseTerminalError,
    DepositReleaseTransientError,
)
from app.services.sms.sms_service import SmsSendError, SmsService, get_sms_service

logger = logging.getLogger(__name__)

_TERMINAL = (ReservationStatus.completed, ReservationStatus.cancelled)


class ReservationValidationError(Exception):
    """Raised when a reservation cannot be created."""


class ReservationStateError(Exception):
    """Raised on an illegal state transition."""


class OutcomeLockedError(Exception):
    """Raised when a party has already used its one outcome change."""


class OutcomeWindowClosedError(Exception):
    """Raised when the correction window has elapsed."""


class YooKassaGateway(Protocol):
    async def cancel_hold(self, *, payment_id: str, idempotence_key: str) -> str: ...


@dataclass(frozen=True, slots=True)
class ReservationDeps:
    yk: YooKassaGateway
    sms: SmsService = field(default_factory=get_sms_service)


def build_reservation(
    *, buyer: User, listing: Listing, now: datetime | None = None
) -> Reservation:
    now = now or datetime.now(UTC)
    if listing.status != ListingStatus.active:
        raise ReservationValidationError("Listing is not active")
    if buyer.id == listing.seller_id:
        raise ReservationValidationError("Cannot reserve your own listing")
    if not buyer.phone_verified:
        raise ReservationValidationError("Phone must be verified")

    reservation = Reservation(
        listing_id=listing.id,
        buyer_id=buyer.id,
        seller_id=listing.seller_id,
        deposit_amount=settings.RESERVATION_DEPOSIT_AMOUNT,
        status=ReservationStatus.pending_payment,
        payment_deadline=now + timedelta(minutes=settings.DEPOSIT_PAYMENT_TTL_MINUTES),
        hold_deadline=now + timedelta(days=settings.RESERVATION_HOLD_DAYS),
    )
    listing.status = ListingStatus.reserved
    return reservation


def confirm_hold(reservation: Reservation) -> None:
    if reservation.status == ReservationStatus.active:
        return
    if reservation.status != ReservationStatus.pending_payment:
        raise ReservationStateError("Hold can be confirmed only from pending_payment")
    reservation.status = ReservationStatus.active


async def _release_deposit(reservation: Reservation, *, deps: ReservationDeps) -> None:
    if not reservation.yk_payment_id or reservation.deposit_released_at is not None:
        return
    due = reservation.deposit_release_due_at
    if due is not None and due > datetime.now(UTC):
        return
    try:
        await deps.yk.cancel_hold(
            payment_id=reservation.yk_payment_id,
            idempotence_key=f"{reservation.id}:release",
        )
    except DepositReleaseTerminalError as exc:
        if reservation.status == ReservationStatus.pending_payment:
            reservation.deposit_released_at = datetime.now(UTC)
            logger.info(
                "deposit.nothing_to_release",
                extra={
                    "reservation_id": str(reservation.id),
                    "yk_payment_id": reservation.yk_payment_id,
                },
            )
        else:
            logger.error(
                "deposit.release_unexpected",
                extra={
                    "reservation_id": str(reservation.id),
                    "yk_payment_id": reservation.yk_payment_id,
                    "err": str(exc),
                },
            )
        return
    except DepositReleaseTransientError as exc:
        logger.warning(
            "deposit.release_deferred",
            extra={"reservation_id": str(reservation.id), "err": str(exc)},
        )
        return
    reservation.deposit_released_at = datetime.now(UTC)


def _budget_used(reservation: Reservation, party: OutcomeParty) -> bool:
    if party is OutcomeParty.buyer:
        return reservation.buyer_change_used
    return reservation.seller_change_used


def _spend_budget(reservation: Reservation, party: OutcomeParty) -> None:
    if party is OutcomeParty.buyer:
        reservation.buyer_change_used = True
    else:
        reservation.seller_change_used = True


async def mark_outcome(
    reservation: Reservation,
    party: OutcomeParty,
    result: ReservationOutcome,
    *,
    deps: ReservationDeps,
    now: datetime | None = None,
) -> None:
    now = now or datetime.now(UTC)
    if reservation.status == ReservationStatus.active:
        reservation.outcome = result
        reservation.outcome_set_by = party
        reservation.outcome_set_at = now
        reservation.status = ReservationStatus.settling
        cap = reservation.hold_deadline
        reservation.correction_deadline = min(
            now + timedelta(hours=settings.OUTCOME_CORRECTION_HOURS), cap
        )
        await _release_deposit(reservation, deps=deps)
        logger.info(
            "reservation.settling",
            extra={"reservation_id": str(reservation.id), "outcome": result.value},
        )
        return
    if reservation.status == ReservationStatus.settling:
        if reservation.correction_deadline and now >= reservation.correction_deadline:
            raise OutcomeWindowClosedError("Correction window has closed")
        if result == reservation.outcome:
            return
        if _budget_used(reservation, party):
            raise OutcomeLockedError("You already changed the outcome once")
        reservation.outcome = result
        _spend_budget(reservation, party)
        return
    raise ReservationStateError(
        "Outcome can be marked only on an active or settling reservation"
    )


def finalize(reservation: Reservation, listing: Listing) -> None:
    if reservation.status != ReservationStatus.settling:
        raise ReservationStateError("Only settling reservations can be finalized")
    reservation.status = ReservationStatus.completed
    listing.status = (
        ListingStatus.sold
        if reservation.outcome == ReservationOutcome.sold
        else ListingStatus.active
    )


async def cancel(
    reservation: Reservation,
    listing: Listing,
    *,
    reason: CancelReason,
    deps: ReservationDeps,
) -> None:
    if reservation.status in _TERMINAL:
        return
    await _release_deposit(reservation, deps=deps)
    reservation.status = ReservationStatus.cancelled
    reservation.cancel_reason = reason
    listing.status = ListingStatus.active
    logger.info(
        "reservation.cancelled",
        extra={"reservation_id": str(reservation.id), "reason": reason.value},
    )


def default_deps() -> ReservationDeps:
    return ReservationDeps(yk=yk)


async def _safe_sms(deps: ReservationDeps, phone: str | None, text: str) -> None:
    if not phone:
        return
    try:
        await deps.sms.send(phone, text)
    except SmsSendError:
        logger.warning("reservation sms failed", extra={"event": "sms_failed"})


class _Handlers:
    def __init__(self, session_factory: Any, redis: Redis) -> None:
        self.session_factory = session_factory
        self.redis = redis
        self.deps = default_deps()

    async def on_hold_confirmed(self, payment_id: str) -> None:
        payment = await yk.find_payment(payment_id)
        if getattr(payment, "status", None) != "waiting_for_capture":
            logger.info(
                "yk webhook: payment not waiting_for_capture on re-fetch, skip",
                extra={"payment_id": payment_id},
            )
            return
        buyer_phone = seller_phone = None
        async with self.session_factory() as session:
            reservation = await res_crud.get_by_payment(session, payment_id)
            if (
                not reservation
                or reservation.status != ReservationStatus.pending_payment
            ):
                return
            confirm_hold(reservation)
            buyer = await session.get(User, reservation.buyer_id)
            seller = await session.get(User, reservation.seller_id)
            buyer_phone = buyer.phone if buyer else None
            seller_phone = seller.phone if seller else None
            await session.commit()
            logger.info(
                "reservation.active (hold confirmed)",
                extra={"reservation_id": str(reservation.id)},
            )
        await _safe_sms(
            self.deps, buyer_phone, "Бронь активна. Выберите время просмотра."
        )
        await _safe_sms(self.deps, seller_phone, "Ваш автомобиль забронирован.")

    async def on_hold_released(self, payment_id: str) -> None:
        async with self.session_factory() as session:
            reservation = await res_crud.get_by_payment(session, payment_id)
            if not reservation or reservation.status in _TERMINAL:
                return
            listing = await listing_crud.get(session, reservation.listing_id)
            booking = await viewings_crud.get_active_booking_for_reservation(
                session, reservation.id
            )
            if booking is not None:
                await viewings_crud.cancel_booking(booking)
            reservation.deposit_released_at = (
                reservation.deposit_released_at or datetime.now(UTC)
            )
            if listing is not None:
                await cancel(
                    reservation,
                    listing,
                    reason=CancelReason.hold_released_externally,
                    deps=self.deps,
                )
            await session.commit()


def build_handlers(session_factory: Any, redis: Redis) -> _Handlers:
    return _Handlers(session_factory, redis)
