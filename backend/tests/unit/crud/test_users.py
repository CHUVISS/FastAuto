from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.users import (
    authenticate,
    create_user,
    delete_user,
    get_user,
    get_user_by_email,
    get_users,
    update_password,
    update_user,
)
from app.models.users import UserRole
from app.schemas.users import PasswordUpdate, UserCreate, UserUpdate

pytestmark = pytest.mark.integration


def _uc(suffix="", role: UserRole = UserRole.user):
    return UserCreate(
        email=f"user{suffix}@example.org",
        password="TestPass123!",
        full_name="Test User",
        role=role,
    )


async def test_get_user_returns_existing(db_session: AsyncSession):
    u = await create_user(db_session, _uc("a"))
    found = await get_user(db_session, u.id)
    assert found is not None
    assert found.id == u.id


async def test_get_user_returns_none_for_missing(db_session: AsyncSession):
    assert await get_user(db_session, uuid.uuid4()) is None


async def test_get_user_by_email_returns_existing(db_session: AsyncSession):
    u = await create_user(db_session, _uc("b"))
    found = await get_user_by_email(db_session, u.email)
    assert found is not None
    assert found.id == u.id


async def test_get_user_by_email_returns_none_for_missing(db_session: AsyncSession):
    assert await get_user_by_email(db_session, "nobody@example.org") is None


async def test_get_user_by_email_is_case_sensitive(db_session: AsyncSession):
    u = await create_user(db_session, _uc("c"))
    result = await get_user_by_email(db_session, u.email.upper())
    assert result is None


async def test_get_users_empty(db_session: AsyncSession):
    users, count = await get_users(db_session)
    assert isinstance(users, list)
    assert count >= 0


async def test_get_users_paginated(db_session: AsyncSession):
    for i in range(3):
        await create_user(db_session, _uc(f"page{i}"))
    all_users, total = await get_users(db_session, limit=100)
    assert total >= 3
    first_page, _ = await get_users(db_session, skip=0, limit=1)
    assert len(first_page) == 1


async def test_create_user_hashes_password(db_session: AsyncSession):
    u = await create_user(db_session, _uc("d"))
    assert u.hashed_password != "TestPass123!"
    assert u.hashed_password.startswith("$argon2")


async def test_create_user_returns_user_with_id(db_session: AsyncSession):
    u = await create_user(db_session, _uc("e"))
    assert u.id is not None
    assert u.email == "usere@example.org"


async def test_create_user_sets_role(db_session: AsyncSession):
    u = await create_user(db_session, _uc("f", role=UserRole.manager))
    assert u.role == UserRole.manager


async def test_update_user_partial(db_session: AsyncSession):
    u = await create_user(db_session, _uc("g"))
    updated = await update_user(db_session, u, UserUpdate(full_name="New Name"))
    assert updated.full_name == "New Name"
    assert updated.email == u.email


async def test_update_user_hashes_new_password(db_session: AsyncSession):
    u = await create_user(db_session, _uc("h"))
    old_hash = u.hashed_password
    updated = await update_user(db_session, u, UserUpdate(password="NewSecure999!"))
    assert updated.hashed_password != old_hash
    assert updated.hashed_password.startswith("$argon2")


async def test_update_password_wrong_current_returns_none(db_session: AsyncSession):
    u = await create_user(db_session, _uc("i"))
    result = await update_password(
        db_session,
        u,
        PasswordUpdate(current_password="WrongPass!", new_password="NewSecure999!"),
    )
    assert result is None


async def test_update_password_success_updates_hash(db_session: AsyncSession):
    u = await create_user(db_session, _uc("j"))
    old_hash = u.hashed_password
    result = await update_password(
        db_session,
        u,
        PasswordUpdate(current_password="TestPass123!", new_password="NewSecure999!"),
    )
    assert result is not None
    assert result.hashed_password != old_hash


async def test_update_password_success_updates_password_changed_at(
    db_session: AsyncSession,
):
    u = await create_user(db_session, _uc("k"))
    old_ts = u.password_changed_at
    result = await update_password(
        db_session,
        u,
        PasswordUpdate(current_password="TestPass123!", new_password="NewSecure999!"),
    )
    assert result is not None
    assert result.password_changed_at >= old_ts


async def test_delete_user_removes_row(db_session: AsyncSession):
    u = await create_user(db_session, _uc("l"))
    uid = u.id
    await delete_user(db_session, u)
    assert await get_user(db_session, uid) is None


async def test_authenticate_valid_credentials(db_session: AsyncSession):
    await create_user(db_session, _uc("m"))
    result = await authenticate(db_session, "userm@example.org", "TestPass123!")
    assert result is not None


async def test_authenticate_wrong_password_returns_none(db_session: AsyncSession):
    await create_user(db_session, _uc("n"))
    result = await authenticate(db_session, "usern@example.org", "WrongPass!")
    assert result is None


async def test_authenticate_missing_user_returns_none(db_session: AsyncSession):
    result = await authenticate(db_session, "noone@example.org", "AnyPass123!")
    assert result is None
