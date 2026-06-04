import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.models.listings import BookingStatus, ViewingBooking


async def create_booking(
    session: AsyncSession,
    *,
    reservation_id: uuid.UUID,
    listing_id: uuid.UUID,
    buyer_id: uuid.UUID,
    window_id: uuid.UUID,
) -> ViewingBooking:
    booking = ViewingBooking(
        reservation_id=reservation_id,
        listing_id=listing_id,
        buyer_id=buyer_id,
        window_id=window_id,
    )
    session.add(booking)
    return booking


async def get_active_booking_for_reservation(
    session: AsyncSession, reservation_id: uuid.UUID
) -> ViewingBooking | None:
    stmt = select(ViewingBooking).where(
        col(ViewingBooking.reservation_id) == reservation_id,
        col(ViewingBooking.status) != BookingStatus.cancelled,
    )
    return (await session.execute(stmt)).scalars().first()


async def cancel_booking(booking: ViewingBooking) -> None:
    booking.status = BookingStatus.cancelled
