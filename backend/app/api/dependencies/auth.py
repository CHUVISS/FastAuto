import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.cache_keys import TTL_USER_AUTH, user_auth_key
from app.core.db import get_session
from app.core.redis import async_get_redis
from app.core.security import verify_token
from app.core.storage import StorageDep
from app.core.token_blacklist import is_token_blacklisted
from app.crud.users import get_user
from app.models.users import User, UserRole, UserStatus

_bearer = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[Redis, Depends(async_get_redis)]
_CredsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _forbidden(detail: str = "Not enough permissions") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _user_to_cache_dict(user: User) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "full_name": user.full_name,
        "email": str(user.email),
        "hashed_password": user.hashed_password,
        "role": str(user.role),
        "status": str(user.status),
        "phone": user.phone,
        "phone_verified": user.phone_verified,
        "phone_visible": user.phone_visible,
        "created_at": user.created_at.isoformat(),
        "password_changed_at": user.password_changed_at.isoformat(),
    }


def _user_from_cache_dict(data: dict[str, Any]) -> User:
    return User(
        id=uuid.UUID(data["id"]),
        full_name=data["full_name"],
        email=data["email"],
        hashed_password=data["hashed_password"],
        role=UserRole(data["role"]),
        status=UserStatus(data["status"]),
        phone=data.get("phone"),
        phone_verified=data.get("phone_verified", False),
        phone_visible=data.get("phone_visible", True),
        created_at=datetime.fromisoformat(data["created_at"]),
        password_changed_at=datetime.fromisoformat(data["password_changed_at"]),
    )


async def get_current_user(
    session: SessionDep,
    redis: RedisDep,
    credentials: _CredsDep,
) -> User:
    if not credentials:
        raise _unauthorized()

    token = credentials.credentials

    if await is_token_blacklisted(redis, token):
        raise _unauthorized("Token has been revoked")

    result = verify_token(token, expected_type="access")
    if not result:
        raise _unauthorized("Token is invalid or expired")

    user_id_str, iat = result

    try:
        uid = uuid.UUID(user_id_str)
    except ValueError:
        raise _unauthorized("Malformed token subject")

    cache_key = user_auth_key(user_id_str)
    cached = await cache_get(redis, cache_key)
    if cached:
        try:
            user = _user_from_cache_dict(cached)
            if user.status != UserStatus.active:
                raise _forbidden("Account is inactive or banned")
            if iat < int(user.password_changed_at.timestamp()):
                raise _unauthorized("Token has been revoked due to password change")
            return user
        except (KeyError, TypeError, ValueError):
            pass

    fetched = await get_user(session, uid)
    if not fetched:
        raise _unauthorized("Token is invalid or expired")
    user = fetched
    if user.status != UserStatus.active:
        raise _forbidden("Account is inactive or banned")
    if iat < int(user.password_changed_at.timestamp()):
        raise _unauthorized("Token has been revoked due to password change")

    await cache_set(redis, cache_key, _user_to_cache_dict(user), TTL_USER_AUTH)

    return user


async def invalidate_user_cache(redis: Redis, user_id: str) -> None:
    await cache_delete(redis, user_auth_key(user_id))


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_optional_user(
    session: SessionDep,
    redis: RedisDep,
    credentials: _CredsDep,
) -> User | None:
    """Resolve the current user if a valid token is present, else ``None``.

    Used by public endpoints that reveal more to an authenticated owner
    (e.g. unmasked VIN on their own listing) without forcing auth.
    """
    if not credentials:
        return None
    try:
        return await get_current_user(session, redis, credentials)
    except HTTPException:
        return None


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def require_role(*allowed_roles: UserRole) -> Callable[..., Any]:
    async def role_checker(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise _forbidden(
                f"Required role: {', '.join(r.value for r in allowed_roles)}"
            )
        return current_user

    return role_checker


AdminUser = Annotated[User, Depends(require_role(UserRole.admin))]
ManagerUser = Annotated[User, Depends(require_role(UserRole.admin, UserRole.manager))]
SupportUser = Annotated[
    User, Depends(require_role(UserRole.admin, UserRole.manager, UserRole.support))
]
ModeratorUser = Annotated[
    User, Depends(require_role(UserRole.admin, UserRole.manager, UserRole.moderator))
]

__all__ = [
    "SessionDep",
    "RedisDep",
    "CurrentUser",
    "OptionalUser",
    "AdminUser",
    "ManagerUser",
    "SupportUser",
    "ModeratorUser",
    "StorageDep",
    "invalidate_user_cache",
]
