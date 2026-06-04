from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token
from app.crud.users import create_user
from app.models.users import UserRole
from app.schemas.users import UserCreate

_DEFAULT_PWD = "TestPass123!"


def _make_user_create(*, role: UserRole, email: str | None = None) -> UserCreate:
    return UserCreate(
        email=email or f"u{uuid.uuid4().hex[:8]}@example.com",
        password=_DEFAULT_PWD,
        full_name=f"Test {role.value.title()}",
        role=role,
    )


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    u = await create_user(db_session, _make_user_create(role=UserRole.admin))
    await db_session.commit()
    return u


@pytest_asyncio.fixture
async def manager_user(db_session: AsyncSession):
    u = await create_user(db_session, _make_user_create(role=UserRole.manager))
    await db_session.commit()
    return u


@pytest_asyncio.fixture
async def support_user(db_session: AsyncSession):
    u = await create_user(db_session, _make_user_create(role=UserRole.support))
    await db_session.commit()
    return u


@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession):
    u = await create_user(db_session, _make_user_create(role=UserRole.user))
    await db_session.commit()
    return u


@pytest.fixture
def access_token(regular_user):
    return create_access_token(str(regular_user.id))


@pytest.fixture
def refresh_token(regular_user):
    return create_refresh_token(str(regular_user.id))


@pytest.fixture
def auth_headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_token(admin_user):
    return create_access_token(str(admin_user.id))


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def manager_token(manager_user):
    return create_access_token(str(manager_user.id))


@pytest.fixture
def manager_headers(manager_token):
    return {"Authorization": f"Bearer {manager_token}"}


@pytest.fixture
def support_token(support_user):
    return create_access_token(str(support_user.id))


@pytest.fixture
def support_headers(support_token):
    return {"Authorization": f"Bearer {support_token}"}
