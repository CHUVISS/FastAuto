from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from app.api.dependencies.auth import (
    CurrentUser,
    RedisDep,
    SessionDep,
    invalidate_user_cache,
)
from app.core.config import settings
from app.core.rate_limit import RateLimit, check_rate_limit
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.token_blacklist import (
    blacklist_auth_pair,
    blacklist_refresh_token,
    blacklist_token,
    is_token_blacklisted,
)
from app.crud.payout import PhoneOtpAuditRepo, phone_owned_by_other
from app.crud.users import authenticate, create_user, get_user, get_user_by_email, update_password
from app.models.users import User
from app.schemas.common import Message
from app.schemas.phone import PhoneSendIn, PhoneVerifyIn
from app.schemas.users import (
    PasswordUpdate,
    Token,
    TokenRefresh,
    UserCreate,
    UserLogin,
    UserPublic,
    UserRegister,
    UserRole,
)
from app.services.otp import otp_service as otp
from app.utils.request import get_client_ip

router = APIRouter(prefix="/auth", tags=["Auth"])

_LOGIN_IP_RULE = RateLimit(scope="auth:login:ip", limit=10, window_sec=60)
_LOGIN_EMAIL_RULE = RateLimit(scope="auth:login:email", limit=5, window_sec=60)
_REGISTER_RULE = RateLimit(scope="auth:register", limit=5, window_sec=300)
_REFRESH_RULE = RateLimit(scope="auth:refresh:ip", limit=30, window_sec=60)


@router.post("/login", response_model=Token, summary="Вход в систему")
async def login(
    request: Request, redis: RedisDep, session: SessionDep, body: UserLogin
) -> Token:
    await check_rate_limit(redis, _LOGIN_IP_RULE, get_client_ip(request))
    await check_rate_limit(redis, _LOGIN_EMAIL_RULE, body.email.lower())
    user = await authenticate(session, email=body.email, password=body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=Token, summary="Обновление токенов")
async def refresh_tokens(
    request: Request, redis: RedisDep, body: TokenRefresh
) -> Token:
    await check_rate_limit(redis, _REFRESH_RULE, get_client_ip(request))
    if await is_token_blacklisted(redis, body.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = verify_token(body.refresh_token, expected_type=settings.TOKEN_TYPE_REFRESH)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id, _ = result

    await blacklist_refresh_token(redis, body.refresh_token)

    return Token(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/logout", response_model=Message, summary="Выход из системы")
async def logout(
    request: Request,
    redis: RedisDep,
    _: CurrentUser,
    body: TokenRefresh | None = None,
) -> Message:
    auth_header = request.headers.get("Authorization", "")
    access_token = auth_header.removeprefix("Bearer ").strip()

    if body and body.refresh_token:
        await blacklist_auth_pair(redis, access_token, body.refresh_token)
    else:
        await blacklist_token(redis, access_token)

    return Message(message="Successfully logged out")


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
)
async def register(
    request: Request, redis: RedisDep, session: SessionDep, body: UserRegister
) -> UserPublic:
    await check_rate_limit(redis, _REGISTER_RULE, get_client_ip(request))
    if await get_user_by_email(session, body.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = await create_user(
        session,
        UserCreate(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            role=UserRole.user,
        ),
    )
    await session.commit()
    return UserPublic.model_validate(user)


@router.get("/me", response_model=UserPublic, summary="Текущий пользователь")
async def get_me(current_user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current_user)


@router.patch("/me/password", response_model=Message, summary="Смена пароля")
async def change_password(
    request: Request,  # noqa: ARG001
    session: SessionDep,
    redis: RedisDep,
    current_user: CurrentUser,
    body: PasswordUpdate,
) -> Message:
    db_user = await get_user(session, current_user.id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated = await update_password(session, db_user, body)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    await session.commit()
    await invalidate_user_cache(redis, str(current_user.id))

    return Message(message="Password updated successfully. Please log in again.")


@router.post("/phone/send-otp", summary="Отправить OTP на телефон")
async def send_phone_otp(
    body: PhoneSendIn,
    current_user: CurrentUser,
    session: SessionDep,
    redis: RedisDep,
) -> dict[str, Any]:
    if body.purpose == "phone_verify":
        if await phone_owned_by_other(session, body.phone, current_user.id):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Phone already linked to another account"
            )
        target_phone = body.phone
    else:
        if not current_user.phone_verified or not current_user.phone:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Verify your phone first")
        target_phone = current_user.phone
    try:
        res = await otp.send_otp(
            current_user,
            target_phone,
            purpose=body.purpose,
            redis=redis,
            audit=PhoneOtpAuditRepo(session),
        )
        await session.commit()
        return res
    except (otp.OtpCooldownError, otp.OtpDailyLimitError, otp.OtpLockedError) as e:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(e)) from e
    except otp.OtpInvalidPhoneError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e


@router.post("/phone/verify-otp", summary="Подтвердить телефон по OTP")
async def verify_phone_otp(
    body: PhoneVerifyIn,
    current_user: CurrentUser,
    session: SessionDep,
    redis: RedisDep,
) -> dict[str, Any]:
    if await phone_owned_by_other(session, body.phone, current_user.id):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Phone already linked to another account"
        )
    db_user = await session.get(User, current_user.id)
    if db_user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    try:
        await otp.verify_otp(
            db_user,
            body.phone,
            body.code,
            purpose="phone_verify",
            redis=redis,
            audit=PhoneOtpAuditRepo(session),
        )
        await session.commit()
        await invalidate_user_cache(redis, str(current_user.id))
        return {"phone_verified": True}
    except otp.OtpExpiredError as e:
        raise HTTPException(status.HTTP_410_GONE, str(e)) from e
    except otp.OtpLockedError as e:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(e)) from e
    except otp.OtpInvalidError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e
