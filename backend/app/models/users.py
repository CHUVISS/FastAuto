import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlalchemy import DateTime, func, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.ai import AiConversation


class UserRole(StrEnum):
    admin = "admin"
    manager = "manager"
    support = "support"
    moderator = "moderator"
    user = "user"


class UserStatus(StrEnum):
    active = "active"
    inactive = "inactive"
    banned = "banned"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    full_name: str = Field(max_length=255)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    role: UserRole = Field(default=UserRole.user)
    status: UserStatus = Field(default=UserStatus.active)
    phone: str | None = Field(default=None, max_length=20, unique=True, index=True)
    phone_verified: bool = Field(
        default=False,
        sa_column_kwargs={"server_default": text("false")},
    )
    phone_visible: bool = Field(
        default=True,
        sa_column_kwargs={"server_default": text("true")},
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"server_default": func.now()},
    )
    password_changed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"server_default": func.now()},
    )

    ai_conversations: list["AiConversation"] = Relationship(back_populates="user")
