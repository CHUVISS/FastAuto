import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, col, func, or_, select

from app.models.reservations import CancelReason, Reservation, ReservationStatus

_TERMINAL = (ReservationStatus.completed, ReservationStatus.cancelled)


async def create(session: AsyncSession, reservation: Reservation) -> Reservation:
    session.add(reservation)
    return reservation


async def get(session: AsyncSession, reservation_id: uuid.UUID) -> Reservation | None:
    return await session.get(Reservation, reservation_id)


async def get_by_payment(session: AsyncSession, payment_id: str) -> Reservation | None:
    stmt = select(Reservation).where(col(Reservation.yk_payment_id) == payment_id)
    return (await session.execute(stmt)).scalars().first()


async def get_active_for_listing(
    session: AsyncSession, listing_id: uuid.UUID
) -> Reservation | None:
    stmt = select(Reservation).where(
        col(Reservation.listing_id) == listing_id,
        col(Reservation.status).notin_(_TERMINAL),
    )
    return (await session.execute(stmt)).scalars().first()


async def has_active_reservation(session: AsyncSession, listing_id: uuid.UUID) -> bool:
    stmt = (
        select(func.count())
        .select_from(Reservation)
        .where(
            col(Reservation.listing_id) == listing_id,
            col(Reservation.status).notin_(_TERMINAL),
        )
    )
    return int((await session.execute(stmt)).scalar_one()) > 0


async def list_for_user(session: AsyncSession, user_id: uuid.UUID) -> list[Reservation]:
    stmt = (
        select(Reservation)
        .where(
            or_(
                col(Reservation.buyer_id) == user_id,
                col(Reservation.seller_id) == user_id,
            )
        )
        .order_by(col(Reservation.created_at).desc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def list_expired_holds(session: AsyncSession, now: datetime) -> list[Reservation]:
    stmt = select(Reservation).where(
        or_(
            and_(
                col(Reservation.status) == ReservationStatus.pending_payment,
                col(Reservation.payment_deadline) < now,
            ),
            and_(
                col(Reservation.status) == ReservationStatus.active,
                col(Reservation.hold_deadline) < now,
            ),
        )
    )
    return list((await session.execute(stmt)).scalars().all())


async def list_settling_due(session: AsyncSession, now: datetime) -> list[Reservation]:
    stmt = select(Reservation).where(
        col(Reservation.status) == ReservationStatus.settling,
        col(Reservation.correction_deadline) < now,
    )
    return list((await session.execute(stmt)).scalars().all())


async def list_prompt_candidates(
    session: AsyncSession, now: datetime, interval: timedelta
) -> list[Reservation]:
    stmt = select(Reservation).where(
        col(Reservation.status) == ReservationStatus.active,
        or_(
            col(Reservation.last_prompt_at).is_(None),
            col(Reservation.last_prompt_at) < now - interval,
        ),
    )
    return list((await session.execute(stmt)).scalars().all())


async def list_release_pending(
    session: AsyncSession, now: datetime
) -> list[Reservation]:
    stmt = select(Reservation).where(
        col(Reservation.status) == ReservationStatus.cancelled,
        col(Reservation.deposit_released_at).is_(None),
        col(Reservation.yk_payment_id).is_not(None),
        or_(
            col(Reservation.deposit_release_due_at).is_(None),
            col(Reservation.deposit_release_due_at) <= now,
        ),
    )
    return list((await session.execute(stmt)).scalars().all())


async def count_active_for_buyer(session: AsyncSession, buyer_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(Reservation)
        .where(
            col(Reservation.buyer_id) == buyer_id,
            col(Reservation.status).notin_(_TERMINAL),
        )
    )
    return int((await session.execute(stmt)).scalar_one())


async def count_buyer_cancels_in_window(
    session: AsyncSession, buyer_id: uuid.UUID, since: datetime
) -> int:
    stmt = (
        select(func.count())
        .select_from(Reservation)
        .where(
            col(Reservation.buyer_id) == buyer_id,
            col(Reservation.status) == ReservationStatus.cancelled,
            col(Reservation.cancel_reason) == CancelReason.buyer_cancelled,
            col(Reservation.created_at) >= since,
        )
    )
    return int((await session.execute(stmt)).scalar_one())
