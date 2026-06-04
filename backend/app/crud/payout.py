import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from app.models.payout import PhoneOTPAudit
from app.models.users import User


class PhoneOtpAuditRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def daily_count(self, user_id: uuid.UUID, since: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(PhoneOTPAudit)
            .where(
                col(PhoneOTPAudit.user_id) == user_id,
                col(PhoneOTPAudit.sent_at) >= since,
            )
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def phone_daily_count(self, phone: str, since: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(PhoneOTPAudit)
            .where(
                col(PhoneOTPAudit.phone) == phone,
                col(PhoneOTPAudit.sent_at) >= since,
            )
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def add(
        self, user_id: uuid.UUID, phone: str, purpose: str, expires_at: datetime
    ) -> None:
        self.session.add(
            PhoneOTPAudit(
                user_id=user_id, phone=phone, purpose=purpose, expires_at=expires_at
            )
        )
        await self.session.flush()

    async def mark_verified(self, user_id: uuid.UUID, phone: str) -> None:
        stmt = (
            select(PhoneOTPAudit)
            .where(
                col(PhoneOTPAudit.user_id) == user_id,
                col(PhoneOTPAudit.phone) == phone,
            )
            .order_by(col(PhoneOTPAudit.sent_at).desc())
            .limit(1)
        )
        row = (await self.session.execute(stmt)).scalars().first()
        if row:
            row.verified = True


async def phone_owned_by_other(
    session: AsyncSession, phone: str, user_id: uuid.UUID
) -> bool:
    stmt = select(User.id).where(col(User.phone) == phone, col(User.id) != user_id)
    return (await session.execute(stmt)).first() is not None
