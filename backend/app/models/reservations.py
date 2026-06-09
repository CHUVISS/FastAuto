import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, Index, func, text
from sqlmodel import Field, SQLModel


class ReservationStatus(StrEnum):
    pending_payment = "pending_payment"  # listing locked, hold not yet confirmed
    active = "active"  # hold confirmed (waiting_for_capture)
    settling = "settling"  # first outcome mark; deposit released; correction open
    completed = "completed"  # finalized (outcome set)
    cancelled = "cancelled"  # released before settle


class ReservationOutcome(StrEnum):
    sold = "sold"
    not_sold = "not_sold"


class OutcomeParty(StrEnum):
    buyer = "buyer"
    seller = "seller"


class CancelReason(StrEnum):
    buyer_cancelled = "buyer_cancelled"
    seller_declined = "seller_declined"
    payment_abandoned = "payment_abandoned"
    hold_expired = "hold_expired"
    hold_released_externally = "hold_released_externally"
    admin = "admin"


class Reservation(SQLModel, table=True):
    __tablename__ = "reservations"
    __table_args__ = (
        Index(
            "uniq_active_reservation_per_listing",
            "listing_id",
            unique=True,
            postgresql_where=text("status NOT IN ('completed','cancelled')"),
        ),
        Index(
            "idx_reservation_hold_deadline",
            "hold_deadline",
            postgresql_where=text("status IN ('pending_payment','active')"),
        ),
        Index(
            "idx_reservation_correction_deadline",
            "correction_deadline",
            postgresql_where=text("status = 'settling'"),
        ),
        Index(
            "idx_reservation_prompt_scan",
            "last_prompt_at",
            postgresql_where=text("status = 'active'"),
        ),
        Index(
            "idx_reservation_release_pending",
            "id",
            postgresql_where=text(
                "status = 'cancelled' AND deposit_released_at IS NULL "
                "AND yk_payment_id IS NOT NULL"
            ),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    listing_id: uuid.UUID = Field(foreign_key="listings.id", ondelete="CASCADE", index=True)
    buyer_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE", index=True)
    seller_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE", index=True)
    deposit_amount: int = Field(sa_type=BigInteger)
    yk_payment_id: str | None = Field(default=None, max_length=50)
    status: ReservationStatus = Field(
        default=ReservationStatus.pending_payment, index=True
    )
    outcome: ReservationOutcome | None = Field(default=None)
    outcome_set_by: OutcomeParty | None = Field(default=None)
    outcome_set_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
    )
    buyer_change_used: bool = Field(
        default=False, sa_column_kwargs={"server_default": text("false")}
    )
    seller_change_used: bool = Field(
        default=False, sa_column_kwargs={"server_default": text("false")}
    )
    deposit_released_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
    )
    cancel_reason: CancelReason | None = Field(default=None)
    payment_deadline: datetime = Field(
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
    )
    hold_deadline: datetime = Field(
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
    )
    correction_deadline: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
    )
    last_prompt_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
    )
    deposit_release_due_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"server_default": func.now()},
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
    )
