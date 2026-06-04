from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.users import User
from app.schemas.users import ProfileUpdate

logger = logging.getLogger(__name__)


async def _check_phone_uniqueness(
    session: AsyncSession, phone: str, exclude_user_id: object
) -> None:
    q = select(User).where(User.phone == phone, User.id != exclude_user_id)
    if (await session.execute(q)).scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Этот номер телефона уже зарегистрирован в системе",
        )


async def update_user_profile(
    session: AsyncSession, user: User, body: ProfileUpdate
) -> User:
    if body.phone is not None:
        await _check_phone_uniqueness(session, body.phone, exclude_user_id=user.id)

    managed = await session.get(User, user.id)
    if managed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if body.full_name is not None:
        managed.full_name = body.full_name
    if body.phone is not None:
        managed.phone = body.phone

    await session.flush()
    await session.refresh(managed)
    logger.info("User %s обновил профиль", managed.id)
    return managed
