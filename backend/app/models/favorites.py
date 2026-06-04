import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, func
from sqlmodel import Field, SQLModel


class Favorite(SQLModel, table=True):
    __tablename__ = "favorites"
    __table_args__ = (
        Index("uniq_favorite_user_listing", "user_id", "listing_id", unique=True),
        Index("idx_favorite_listing", "listing_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE", index=True)
    listing_id: uuid.UUID = Field(foreign_key="listings.id", ondelete="CASCADE")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"server_default": func.now()},
    )
