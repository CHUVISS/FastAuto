from __future__ import annotations

from datetime import date

from sqlmodel import col, func, select

from app.core.db import async_session_factory
from app.models.listings import Listing, ListingStatus
from app.models.reservations import Reservation, ReservationStatus
from app.models.tickets import Ticket, TicketStatus
from app.models.users import User
from app.schemas.admin import DashboardStats


async def get_dashboard_stats(
    date_from: date | None = None,
    date_to: date | None = None,
) -> DashboardStats:
    async with async_session_factory() as s:
        listing_row = (
            await s.execute(
                select(
                    func.count().label("total"),
                    func.count()
                    .filter(Listing.status == ListingStatus.active)  # type: ignore[call-overload]
                    .label("active"),
                    func.count()
                    .filter(Listing.status == ListingStatus.reserved)  # type: ignore[call-overload]
                    .label("reserved"),
                    func.count()
                    .filter(Listing.status == ListingStatus.sold)  # type: ignore[call-overload]
                    .label("sold"),
                ).select_from(Listing)
            )
        ).one()

        res_q = select(
            func.count().label("total"),
            func.count()
            .filter(Reservation.status == ReservationStatus.active)  # type: ignore[call-overload]
            .label("active"),
            func.count()
            .filter(Reservation.status == ReservationStatus.settling)  # type: ignore[call-overload]
            .label("settling"),
            func.count()
            .filter(Reservation.status == ReservationStatus.completed)  # type: ignore[call-overload]
            .label("completed"),
        ).select_from(Reservation)
        if date_from:
            res_q = res_q.where(col(Reservation.created_at) >= date_from)
        if date_to:
            res_q = res_q.where(col(Reservation.created_at) <= date_to)
        res_row = (await s.execute(res_q)).one()

        user_count = (
            await s.execute(select(func.count()).select_from(User))
        ).scalar_one()

        open_tickets = (
            await s.execute(
                select(func.count())
                .select_from(Ticket)
                .where(
                    col(Ticket.status).in_(
                        [TicketStatus.open, TicketStatus.in_progress]
                    )
                )
            )
        ).scalar_one()

    return DashboardStats(
        total_listings=listing_row.total,
        active_listings=listing_row.active,
        reserved_listings=listing_row.reserved,
        sold_listings=listing_row.sold,
        total_reservations=res_row.total,
        active_reservations=res_row.active,
        settling_reservations=res_row.settling,
        completed_reservations=res_row.completed,
        total_users=user_count,
        open_tickets=open_tickets,
    )
