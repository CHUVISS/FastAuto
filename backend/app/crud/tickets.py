import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.models.tickets import Ticket, TicketMessage, TicketStatus, TicketType


async def create(session: AsyncSession, ticket: Ticket) -> Ticket:
    session.add(ticket)
    return ticket


async def get(session: AsyncSession, ticket_id: uuid.UUID) -> Ticket | None:
    return await session.get(Ticket, ticket_id)


async def add_message(session: AsyncSession, message: TicketMessage) -> TicketMessage:
    session.add(message)
    return message


async def list_messages(
    session: AsyncSession, ticket_id: uuid.UUID
) -> list[TicketMessage]:
    stmt = (
        select(TicketMessage)
        .where(col(TicketMessage.ticket_id) == ticket_id)
        .order_by(col(TicketMessage.created_at))
    )
    return list((await session.execute(stmt)).scalars().all())


async def list_all(
    session: AsyncSession,
    *,
    type: TicketType | None = None,
    status: TicketStatus | None = None,
) -> list[Ticket]:
    stmt = select(Ticket)
    if type is not None:
        stmt = stmt.where(col(Ticket.type) == type)
    if status is not None:
        stmt = stmt.where(col(Ticket.status) == status)
    stmt = stmt.order_by(col(Ticket.created_at).desc())
    return list((await session.execute(stmt)).scalars().all())


async def list_for_user(session: AsyncSession, user_id: uuid.UUID) -> list[Ticket]:
    stmt = (
        select(Ticket)
        .where(col(Ticket.creator_id) == user_id)
        .order_by(col(Ticket.created_at).desc())
    )
    return list((await session.execute(stmt)).scalars().all())
