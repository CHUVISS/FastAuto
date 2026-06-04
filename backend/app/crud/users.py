from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.crud.base import apply_partial_update, flush_refresh, get_by_pk
from app.models.users import User
from app.schemas.users import PasswordUpdate, UserCreate, UserUpdate


async def get_user(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await get_by_pk(session, User, user_id)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_users(
    session: AsyncSession,
    *,
    skip: int = 0,
    limit: int | None = None,
) -> tuple[list[User], int]:
    effective_limit = limit if limit is not None else settings.PAGINATION_DEFAULT_LIMIT
    count_result = await session.execute(select(func.count()).select_from(User))
    count = count_result.scalar_one()
    result = await session.execute(
        select(User)
        .order_by(col(User.created_at).desc())
        .offset(skip)
        .limit(effective_limit)
    )
    return list(result.scalars().all()), count


async def create_user(session: AsyncSession, user_in: UserCreate) -> User:
    user = User.model_validate(
        user_in,
        update={"hashed_password": await hash_password(user_in.password)},
    )
    session.add(user)
    return await flush_refresh(session, user)


async def update_user(
    session: AsyncSession, db_user: User, user_in: UserUpdate
) -> User:
    data = user_in.model_dump(exclude_unset=True)
    if "password" in data:
        data["hashed_password"] = await hash_password(data.pop("password"))
    return await apply_partial_update(session, db_user, data)


async def update_password(
    session: AsyncSession,
    db_user: User,
    body: PasswordUpdate,
) -> User | None:
    if not await verify_password(body.current_password, db_user.hashed_password):
        return None
    db_user.hashed_password = await hash_password(body.new_password)
    db_user.password_changed_at = datetime.now(UTC)
    session.add(db_user)
    return await flush_refresh(session, db_user)


async def delete_user(session: AsyncSession, db_user: User) -> None:
    await session.delete(db_user)
    await session.flush()


async def authenticate(session: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(session, email)
    if not user:
        await hash_password("dummy-prevent-timing-attack")
        return None
    if not await verify_password(password, user.hashed_password):
        return None
    return user
