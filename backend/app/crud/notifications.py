import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select, update

from app.models.notifications import Notification


async def create(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    notif_type: str,
    payload: dict[str, Any] | None = None,
) -> Notification:
    notification = Notification(user_id=user_id, type=notif_type, payload=payload or {})
    session.add(notification)
    return notification


async def get(session: AsyncSession, notification_id: uuid.UUID) -> Notification | None:
    return await session.get(Notification, notification_id)


async def list_for_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    unread_only: bool = False,
    limit: int = 50,
) -> list[Notification]:
    stmt = select(Notification).where(col(Notification.user_id) == user_id)
    if unread_only:
        stmt = stmt.where(col(Notification.read_at).is_(None))
    stmt = stmt.order_by(col(Notification.created_at).desc()).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def mark_all_read(session: AsyncSession, user_id: uuid.UUID) -> int:
    stmt = (
        update(Notification)
        .where(
            col(Notification.user_id) == user_id,
            col(Notification.read_at).is_(None),
        )
        .values(read_at=datetime.now(UTC))
    )
    result = await session.execute(stmt)
    return int(getattr(result, "rowcount", 0) or 0)
