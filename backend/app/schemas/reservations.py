import uuid

from pydantic import BaseModel, Field

from app.models.reservations import ReservationOutcome


class ReserveIn(BaseModel):
    listing_id: uuid.UUID
    window_id: uuid.UUID | None = None


class BookViewingIn(BaseModel):
    window_id: uuid.UUID


class OutcomeIn(BaseModel):
    result: ReservationOutcome


class DeclineIn(BaseModel):
    reason: str = Field(min_length=1, max_length=300)
