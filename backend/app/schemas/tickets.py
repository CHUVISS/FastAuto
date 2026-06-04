import uuid

from pydantic import BaseModel

from app.models.tickets import TicketStatus, TicketType


class TicketCreate(BaseModel):
    type: TicketType
    title: str
    listing_id: uuid.UUID | None = None
    reservation_id: uuid.UUID | None = None


class TicketMessageCreate(BaseModel):
    body: str


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    assignee_id: uuid.UUID | None = None
