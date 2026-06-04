import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies.auth import CurrentUser, SessionDep, SupportUser
from app.crud import tickets as crud
from app.models.tickets import Ticket, TicketMessage, TicketStatus, TicketType
from app.models.users import User, UserRole
from app.schemas.tickets import TicketCreate, TicketMessageCreate, TicketUpdate

router = APIRouter(prefix="/tickets", tags=["tickets"])

_STAFF = {UserRole.support, UserRole.manager, UserRole.admin}


def _can_view(ticket: Ticket, user: User) -> bool:
    return user.id in (ticket.creator_id, ticket.assignee_id) or user.role in _STAFF


@router.post("", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_ticket(
    body: TicketCreate, user: CurrentUser, session: SessionDep
) -> Ticket:
    ticket = Ticket(creator_id=user.id, **body.model_dump(exclude_none=True))
    await crud.create(session, ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


@router.get("/my", response_model=None)
async def my_tickets(user: CurrentUser, session: SessionDep) -> list[Ticket]:
    return await crud.list_for_user(session, user.id)


@router.get("", response_model=None)
async def list_tickets(
    _: SupportUser,
    session: SessionDep,
    type: TicketType | None = Query(None),
    status: TicketStatus | None = Query(None),
) -> list[Ticket]:
    return await crud.list_all(session, type=type, status=status)


@router.get("/{ticket_id}", response_model=None)
async def get_ticket(
    ticket_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> dict[str, Any]:
    ticket = await crud.get(session, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if not _can_view(ticket, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    messages = await crud.list_messages(session, ticket.id)
    return {"ticket": ticket, "messages": messages}


@router.post(
    "/{ticket_id}/messages", status_code=status.HTTP_201_CREATED, response_model=None
)
async def add_message(
    ticket_id: uuid.UUID,
    body: TicketMessageCreate,
    user: CurrentUser,
    session: SessionDep,
) -> TicketMessage:
    ticket = await crud.get(session, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if not _can_view(ticket, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    msg = await crud.add_message(
        session, TicketMessage(ticket_id=ticket.id, sender_id=user.id, body=body.body)
    )
    await session.commit()
    await session.refresh(msg)
    return msg


@router.patch("/{ticket_id}", response_model=None)
async def update_ticket(
    ticket_id: uuid.UUID,
    body: TicketUpdate,
    _: SupportUser,
    session: SessionDep,
) -> Ticket:
    ticket = await crud.get(session, ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(ticket, key, value)
    await session.commit()
    await session.refresh(ticket)
    return ticket
