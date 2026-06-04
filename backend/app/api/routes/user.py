from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.dependencies.auth import (
    CurrentUser,
    RedisDep,
    SessionDep,
    invalidate_user_cache,
)
from app.schemas.users import ProfileUpdate, UserPublic
from app.services.profile.profile_service import update_user_profile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["User (личный кабинет)"])


@router.get("/profile", response_model=UserPublic, summary="Мой профиль")
async def get_profile(current_user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current_user)


@router.patch("/profile", response_model=UserPublic, summary="Обновить профиль")
async def update_profile(
    session: SessionDep,
    redis: RedisDep,
    current_user: CurrentUser,
    body: ProfileUpdate,
) -> UserPublic:
    user = await update_user_profile(session, current_user, body)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Этот номер телефона уже зарегистрирован в системе",
        )
    await invalidate_user_cache(redis, str(current_user.id))
    return UserPublic.model_validate(user)
