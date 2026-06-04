import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, func, text
from sqlmodel import Field, SQLModel


class PhoneOTPAudit(SQLModel, table=True):
    __tablename__ = "phone_otp_audit"
    __table_args__ = (
        Index("idx_otp_audit_user_sent", "user_id", "sent_at"),
        Index("idx_otp_audit_phone_sent", "phone", "sent_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    phone: str = Field(max_length=20)
    purpose: str = Field(default="phone_verify", max_length=20)
    sent_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"server_default": func.now()},
    )
    expires_at: datetime = Field(
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
    )
    attempts: int = Field(default=0)
    verified: bool = Field(
        default=False, sa_column_kwargs={"server_default": text("false")}
    )
