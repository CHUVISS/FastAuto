"""User preference model for AI recommendation weight engine."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel


class UserPreference(SQLModel, table=True):
    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "tag_type", "tag_value", name="uq_user_pref"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE", index=True)
    tag_type: str = Field(max_length=50, index=True)    # brand | body_type | fuel_type
    tag_value: str = Field(max_length=100, index=True)  # BMW  | suv       | petrol
    weight: float = Field(default=1.0)
    count: int = Field(default=1)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
    )
