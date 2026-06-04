import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings

_password_hash = PasswordHash((Argon2Hasher(),))


def _create_token(
    subject: str | Any,
    secret_key: str,
    token_type: str,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(UTC)
    expire = now + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "iat": int(now.timestamp()),
        "exp": expire,
        "sub": str(subject),
        "type": token_type,
    }

    return jwt.encode(payload, secret_key, algorithm=settings.ALGORITHM)


def create_access_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    return _create_token(
        subject=subject,
        secret_key=settings.SECRET_KEY,
        token_type=settings.TOKEN_TYPE_ACCESS,
        expires_delta=expires_delta,
    )


def create_refresh_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    return _create_token(
        subject=subject,
        secret_key=settings.REFRESH_SECRET_KEY,
        token_type=settings.TOKEN_TYPE_REFRESH,
        expires_delta=expires_delta
        or timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    )


def verify_token(
    token: str, expected_type: str | None = None
) -> tuple[str, int] | None:
    secret_key = (
        settings.REFRESH_SECRET_KEY
        if expected_type == settings.TOKEN_TYPE_REFRESH
        else settings.SECRET_KEY
    )
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub", "type", "iat"]},
        )

        if expected_type and payload.get("type") != expected_type:
            return None

        return str(payload["sub"]), int(payload["iat"])
    except jwt.PyJWTError:
        return None


async def hash_password(password: str) -> str:
    return await asyncio.to_thread(_password_hash.hash, password)


async def verify_password(plain: str, hashed: str) -> bool:
    verified, _ = await asyncio.to_thread(
        _password_hash.verify_and_update, plain, hashed
    )
    return verified
