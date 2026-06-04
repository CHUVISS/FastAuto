from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.users import create_user
from app.models.users import UserRole
from app.schemas.users import ProfileUpdate, UserCreate
from app.services.profile.profile_service import update_user_profile

pytestmark = pytest.mark.integration


async def _make_user(
    session: AsyncSession, email: str = "profile@example.org", phone: str | None = None
):
    u = await create_user(
        session,
        UserCreate(
            email=email,
            password="Pass123!",
            full_name="Original Name",
            role=UserRole.user,
        ),
    )
    if phone:
        u.phone = phone
        await session.flush()
    return u


async def test_update_profile_name(db_session: AsyncSession):
    user = await _make_user(db_session)
    result = await update_user_profile(
        db_session, user, ProfileUpdate(full_name="New Name")
    )
    assert result.full_name == "New Name"


async def test_update_profile_phone(db_session: AsyncSession):
    user = await _make_user(db_session)
    result = await update_user_profile(
        db_session, user, ProfileUpdate(phone="79001234567")
    )
    assert result.phone == "79001234567"


async def test_update_profile_phone_conflict_with_other_user_raises(
    db_session: AsyncSession,
):
    other = await _make_user(db_session, email="other@example.org", phone="79009990001")
    user = await _make_user(db_session, email="me@example.org")
    with pytest.raises(HTTPException) as exc:
        await update_user_profile(db_session, user, ProfileUpdate(phone=other.phone))
    assert exc.value.status_code == 409


async def test_update_profile_own_phone_allowed(db_session: AsyncSession):
    user = await _make_user(db_session, phone="79009990003")
    result = await update_user_profile(
        db_session, user, ProfileUpdate(phone="79009990003")
    )
    assert result.phone == "79009990003"


async def test_update_profile_no_fields_unchanged(db_session: AsyncSession):
    user = await _make_user(db_session)
    original_name = user.full_name
    result = await update_user_profile(db_session, user, ProfileUpdate())
    assert result.full_name == original_name
