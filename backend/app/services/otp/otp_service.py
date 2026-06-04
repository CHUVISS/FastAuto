import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings
from app.models.users import User

logger = logging.getLogger(__name__)


class OtpCooldownError(Exception): ...


class OtpDailyLimitError(Exception): ...


class OtpLockedError(Exception): ...


class OtpExpiredError(Exception): ...


class OtpInvalidError(Exception): ...


class OtpInvalidPhoneError(Exception):
    """SMS provider rejected the destination phone (not deliverable)"""


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def _keys(purpose: str, uid: str) -> dict[str, str]:
    return {
        "otp": f"otp:{purpose}:{uid}",
        "cooldown": f"otp_cooldown:{purpose}:{uid}",
        "lockout": f"otp_lockout:{purpose}:{uid}",
        "attempts": f"otp_attempts:{purpose}:{uid}",
    }


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return value.decode() if isinstance(value, bytes) else str(value)


async def send_otp(
    user: User,
    phone: str,
    *,
    purpose: str = "phone_verify",
    redis: Redis,
    audit: Any,
    env: str | None = None,
) -> dict[str, Any]:
    env = env or settings.ENVIRONMENT
    uid = str(user.id)
    k = _keys(purpose, uid)

    if await redis.get(k["lockout"]):
        raise OtpLockedError("Too many attempts; try later")
    since = datetime.now(UTC) - timedelta(hours=24)
    if await audit.daily_count(user.id, since) >= settings.OTP_MAX_DAILY:
        raise OtpDailyLimitError("Daily SMS limit reached")
    if await audit.phone_daily_count(phone, since) >= settings.OTP_MAX_DAILY:
        raise OtpDailyLimitError("Daily SMS limit for this number reached")
    if not await redis.set(
        k["cooldown"], "1", ex=settings.OTP_COOLDOWN_SECONDS, nx=True
    ):
        raise OtpCooldownError("Please wait before requesting another code")

    code = f"{secrets.randbelow(1_000_000):06d}"
    await redis.set(k["otp"], _hash(code), ex=settings.OTP_TTL_SECONDS)
    await redis.delete(k["attempts"])
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.OTP_TTL_SECONDS)
    await audit.add(user.id, phone, purpose, expires_at)

    from app.services.sms.sms_service import (
        SmsProviderUnavailableError,
        SmsRejectedError,
        get_sms_service,
    )

    try:
        await get_sms_service().send(phone, f"Код подтверждения: {code}")
    except SmsRejectedError as e:
        raise OtpInvalidPhoneError(e.reason) from e
    except SmsProviderUnavailableError:
        logger.warning("SMS provider unavailable while sending OTP to %s", phone)

    out: dict[str, Any] = {"sent": True}
    if env == "local":
        out["debug_otp"] = code
    return out


async def verify_otp(
    user: User,
    phone: str,
    code: str,
    *,
    purpose: str = "phone_verify",
    redis: Redis,
    audit: Any,
) -> bool:
    uid = str(user.id)
    k = _keys(purpose, uid)

    if await redis.get(k["lockout"]):
        raise OtpLockedError("Locked")
    stored = _as_str(await redis.get(k["otp"]))
    if stored is None:
        raise OtpExpiredError("Code expired")
    if _hash(code) != stored:
        attempts = await redis.incr(k["attempts"])
        if attempts >= settings.OTP_MAX_ATTEMPTS:
            await redis.set(k["lockout"], "1", ex=settings.OTP_LOCKOUT_SECONDS)
            await redis.delete(k["otp"], k["attempts"])
        raise OtpInvalidError("Invalid code")

    await redis.delete(k["otp"], k["attempts"])
    if purpose == "phone_verify":
        user.phone = phone
        user.phone_verified = True
        await audit.mark_verified(user.id, phone)
    return True
