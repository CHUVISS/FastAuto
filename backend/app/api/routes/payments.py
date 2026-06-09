import logging
import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis

from app.api.dependencies.auth import RedisDep, SessionDep
from app.core.config import settings
from app.core.db import async_session_factory
from app.crud import reservations as res_crud
from app.crud import listings as listing_crud
from app.models.listings import ListingStatus
from app.models.reservations import Reservation, ReservationStatus
from app.schemas.payments import ReturnStatus
from app.services.payments import yookassa_service as yk
from app.services.payments.errors import PaymentLookupError
from app.services.reservations.reservation_service import build_handlers, confirm_hold

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])

_HOLD_CONFIRMED = "waiting_for_capture"


@router.get("/fake-confirm", include_in_schema=False, response_model=None)
async def fake_payment_confirm(
    reservation_id: uuid.UUID,
    session: SessionDep,
) -> RedirectResponse:
    """Auto-confirms a reservation in fake payment mode (no real YooKassa)."""
    if not yk._fake_mode():
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    reservation = await res_crud.get(session, reservation_id)
    if reservation and reservation.status == ReservationStatus.pending_payment:
        listing = await listing_crud.get(session, reservation.listing_id)
        if listing:
            listing.status = ListingStatus.reserved
        confirm_hold(reservation)
        await session.commit()
        logger.info("fake payment confirmed", extra={"reservation_id": str(reservation_id)})

    target = (
        f"{settings.FRONTEND_BASE_URL.rstrip('/')}/payment/return"
        f"?reservation_id={reservation_id}&status=ok"
    )
    return RedirectResponse(url=target, status_code=303)


@router.get("/return", include_in_schema=False, response_model=None)
async def yookassa_return(
    reservation_id: uuid.UUID,
    session: SessionDep,
    redis: RedisDep,
) -> RedirectResponse:
    status_q = ReturnStatus.failed
    reservation = await res_crud.get(session, reservation_id)
    if reservation is not None:
        status_q = await _resolve_status(reservation, redis)
    target = (
        f"{settings.FRONTEND_BASE_URL.rstrip('/')}/payment/return"
        f"?reservation_id={reservation_id}&status={status_q.value}"
    )
    return RedirectResponse(url=target, status_code=303)


async def _resolve_status(reservation: Reservation, redis: Redis) -> ReturnStatus:
    if reservation.status == ReservationStatus.active:
        return ReturnStatus.ok
    if reservation.status == ReservationStatus.cancelled:
        return ReturnStatus.cancelled
    if reservation.status != ReservationStatus.pending_payment:
        return ReturnStatus.failed
    if not reservation.yk_payment_id:
        return ReturnStatus.pending
    try:
        payment = await yk.find_payment(reservation.yk_payment_id)
    except PaymentLookupError:
        logger.warning(
            "payments.return.lookup_failed",
            extra={"reservation_id": str(reservation.id)},
        )
        return ReturnStatus.pending
    if getattr(payment, "status", None) == _HOLD_CONFIRMED:
        handlers = build_handlers(async_session_factory, redis)
        await handlers.on_hold_confirmed(reservation.yk_payment_id)
        logger.info(
            "payments.return.confirmed",
            extra={"reservation_id": str(reservation.id)},
        )
        return ReturnStatus.ok
    return ReturnStatus.pending
