import uuid
from datetime import UTC, date, datetime, time
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, Index, func, text
from sqlmodel import Field, SQLModel


class ListingStatus(StrEnum):
    draft = "draft"
    pending_review = "pending_review"
    active = "active"
    reserved = "reserved"
    sold = "sold"
    archived = "archived"


class Condition(StrEnum):
    excellent = "excellent"
    good = "good"
    fair = "fair"
    poor = "poor"


class BookingStatus(StrEnum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


_ACTIVE = text("status = 'active'")


class Listing(SQLModel, table=True):
    __tablename__ = "listings"
    __table_args__ = (
        Index("idx_listings_seller", "seller_id"),
        Index(
            "uniq_active_vin",
            "vin",
            unique=True,
            postgresql_where=text("vin IS NOT NULL"),
        ),
        Index("idx_active_recency", "created_at", "id", postgresql_where=_ACTIVE),
        Index(
            "idx_active_mark_recency",
            "mark_id",
            "created_at",
            "id",
            postgresql_where=_ACTIVE,
        ),
        Index(
            "idx_active_model_recency",
            "model_id",
            "created_at",
            "id",
            postgresql_where=_ACTIVE,
        ),
        Index("idx_active_price", "price", "id", postgresql_where=_ACTIVE),
        Index(
            "idx_active_mark_price", "mark_id", "price", "id", postgresql_where=_ACTIVE
        ),
        Index(
            "idx_active_model_price",
            "model_id",
            "price",
            "id",
            postgresql_where=_ACTIVE,
        ),
        Index("idx_listings_expiry_active", "expires_at", postgresql_where=_ACTIVE),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    seller_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    modification_id: str = Field(max_length=100, foreign_key="catalog.modifications.id")
    mark_id: str = Field(max_length=50)
    model_id: str = Field(max_length=100)
    body_type: str | None = Field(default=None, max_length=50)
    engine_type: str | None = Field(default=None, max_length=50)
    year: int
    price: int = Field(sa_type=BigInteger)
    mileage: int
    color_id: str = Field(max_length=30, foreign_key="catalog.colors.id")
    vin: str | None = Field(default=None, max_length=17)
    license_plate: str | None = Field(default=None, max_length=10)
    license_plate_edit_count: int = Field(default=0)
    description: str | None = Field(default=None)
    condition: Condition
    city_id: str = Field(max_length=13, foreign_key="geo.cities.id")
    sale_address: str | None = Field(default=None, max_length=300)
    accepts_cash: bool = Field(
        default=False, sa_column_kwargs={"server_default": text("false")}
    )
    accepts_transfer: bool = Field(
        default=False, sa_column_kwargs={"server_default": text("false")}
    )
    status: ListingStatus = Field(default=ListingStatus.draft)
    viewing_enabled: bool = Field(
        default=True, sa_column_kwargs={"server_default": text("true")}
    )
    viewing_repeat_weekly: bool = Field(
        default=False, sa_column_kwargs={"server_default": text("false")}
    )
    published_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
    )
    expires_at: datetime | None = Field(
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


class ListingImage(SQLModel, table=True):
    __tablename__ = "listing_images"
    __table_args__ = (
        Index(
            "uniq_primary_image",
            "listing_id",
            unique=True,
            postgresql_where=text("is_primary = true"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    listing_id: uuid.UUID = Field(
        foreign_key="listings.id", ondelete="CASCADE", index=True
    )
    url: str
    thumbnail_url: str
    is_primary: bool = Field(
        default=False, sa_column_kwargs={"server_default": text("false")}
    )
    sort_order: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"server_default": func.now()},
    )


class ViewingWindow(SQLModel, table=True):
    __tablename__ = "viewing_windows"
    __table_args__ = (
        Index("idx_viewing_windows_listing_date", "listing_id", "window_date"),
        Index(
            "uniq_window_slot",
            "listing_id",
            "window_date",
            "time_from",
            "time_to",
            unique=True,
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    listing_id: uuid.UUID = Field(foreign_key="listings.id", ondelete="CASCADE")
    window_date: date
    time_from: time
    time_to: time
    is_available: bool = Field(
        default=True, sa_column_kwargs={"server_default": text("true")}
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"server_default": func.now()},
    )


class ViewingBooking(SQLModel, table=True):
    __tablename__ = "viewing_bookings"
    __table_args__ = (
        Index(
            "uniq_active_booking",
            "listing_id",
            "window_id",
            unique=True,
            postgresql_where=text("status != 'cancelled'"),
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    listing_id: uuid.UUID = Field(foreign_key="listings.id", ondelete="CASCADE")
    buyer_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    window_id: uuid.UUID | None = Field(default=None, foreign_key="viewing_windows.id")
    reservation_id: uuid.UUID | None = Field(
        default=None, foreign_key="reservations.id", index=True
    )
    status: BookingStatus = Field(default=BookingStatus.scheduled)
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
