from __future__ import annotations

import uuid

from app.models.users import UserRole
from app.schemas.users import UserCreate

_DEFAULT_PWD = "TestPass123!"


def make_user_create(
    *,
    email: str | None = None,
    password: str = _DEFAULT_PWD,
    full_name: str = "Test User",
    role: UserRole = UserRole.user,
) -> UserCreate:
    return UserCreate(
        email=email or f"u{uuid.uuid4().hex[:8]}@test.local",
        password=password,
        full_name=full_name,
        role=role,
    )
