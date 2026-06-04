from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime

import jwt
from fastapi import HTTPException, status
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

BLACKLIST_PREFIX = "blacklist:token:"


class AuthBackendUnavailable(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service temporarily unavailable",
            headers={"Retry-After": "5"},
        )


def token_key(token: str) -> str:
    digest = hashlib.sha256(token.encode()).hexdigest()
    return f"{BLACKLIST_PREFIX}{digest}"


def _decode_exp(token: str, secret: str) -> int:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
        exp = payload.get("exp")
        if exp is None:
            return 1
        remaining = int(exp - datetime.now(UTC).timestamp())
        return max(remaining, 1)
    except jwt.PyJWTError:
        return 1


def _access_ttl(token: str) -> int:
    return _decode_exp(token, settings.SECRET_KEY)


def _refresh_ttl(token: str) -> int:
    return _decode_exp(token, settings.REFRESH_SECRET_KEY)


async def blacklist_token(redis: Redis, token: str) -> None:
    key = token_key(token)
    ttl = _access_ttl(token)
    try:
        await redis.setex(key, ttl, "1")
        logger.debug("Token blacklisted (ttl=%ds)", ttl)
    except Exception as exc:
        logger.warning("Failed to blacklist token: %s", exc)


async def blacklist_refresh_token(redis: Redis, token: str) -> None:
    key = token_key(token)
    ttl = _refresh_ttl(token)
    try:
        await redis.setex(key, ttl, "1")
        logger.debug("Refresh token blacklisted (ttl=%ds)", ttl)
    except Exception as exc:
        logger.warning("Failed to blacklist refresh token: %s", exc)


async def blacklist_auth_pair(
    redis: Redis, access_token: str, refresh_token: str
) -> None:
    try:
        pipe = redis.pipeline()
        await pipe.setex(token_key(access_token), _access_ttl(access_token), "1")
        await pipe.setex(token_key(refresh_token), _refresh_ttl(refresh_token), "1")
        await pipe.execute()
        logger.info(
            "Auth pair blacklisted (access_ttl=%ds, refresh_ttl=%ds)",
            _access_ttl(access_token),
            _refresh_ttl(refresh_token),
        )
    except Exception as exc:
        logger.warning("Failed to blacklist auth pair: %s", exc)


async def is_token_blacklisted(redis: Redis, token: str) -> bool:
    try:
        return bool(await redis.exists(token_key(token)))
    except Exception as exc:
        # Redis unavailable — fail open. Tokens are still protected by the
        # password_changed_at check in get_current_user (DB-based), so
        # returning False here does not bypass security for password changes.
        logger.error("Redis unavailable during token blacklist check: %s", exc)
        return False
