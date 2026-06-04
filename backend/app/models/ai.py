import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Index, Text, func
from sqlmodel import Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.users import User


class AiMessageRole(StrEnum):
    user = "user"
    assistant = "assistant"
    tool = "tool"


class AiConversation(SQLModel, table=True):
    __tablename__ = "ai_conversations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE", index=True)
    title: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"server_default": func.now()},
    )
    last_message_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"server_default": func.now()},
    )

    user: Optional["User"] = Relationship(back_populates="ai_conversations")
    messages: list["AiMessage"] = Relationship(
        back_populates="conversation",
        cascade_delete=True,
    )


class AiMessage(SQLModel, table=True):
    __tablename__ = "ai_messages"
    __table_args__ = (
        Index("ix_ai_messages_conversation_id", "conversation_id"),
        Index("ix_ai_messages_created_at", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(
        foreign_key="ai_conversations.id", ondelete="CASCADE"
    )
    role: AiMessageRole
    content: str = Field(sa_column=Column(Text, nullable=False))
    input_tokens: int | None = None
    output_tokens: int | None = None
    model_name: str | None = Field(default=None, max_length=100)
    finish_reason: str | None = Field(default=None, max_length=50)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"server_default": func.now()},
    )

    conversation: AiConversation | None = Relationship(back_populates="messages")
    tool_calls: list["AiToolCall"] = Relationship(
        back_populates="message",
        cascade_delete=True,
    )


class AiToolCall(SQLModel, table=True):
    __tablename__ = "ai_tool_calls"
    __table_args__ = (Index("ix_ai_tool_calls_message_id", "message_id"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    message_id: uuid.UUID = Field(foreign_key="ai_messages.id", ondelete="CASCADE")
    tool_name: str = Field(max_length=100)
    arguments: str = Field(sa_column=Column(Text, nullable=False))
    result: str | None = Field(default=None, sa_column=Column(Text))
    error: str | None = Field(default=None, max_length=500)
    duration_ms: int | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"server_default": func.now()},
    )

    message: Optional["AiMessage"] = Relationship(back_populates="tool_calls")
