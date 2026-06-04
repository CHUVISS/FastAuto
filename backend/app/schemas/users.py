from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.models.users import UserRole as UserRole
from app.models.users import UserStatus as UserStatus
from app.schemas.common import normalize_russian_phone

# Admin


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    role: UserRole | None = None
    status: UserStatus | None = None
    password: str | None = None


class UserPublic(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole
    status: UserStatus
    phone: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UsersPublic(BaseModel):
    data: list[UserPublic]
    count: int


# Auth


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str


# Profile


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None

    @field_validator("phone", check_fields=False)
    @classmethod
    def validate_phone_format(cls, v: str | None) -> str | None:
        return normalize_russian_phone(v)
