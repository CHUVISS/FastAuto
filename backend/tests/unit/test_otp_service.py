import uuid

import pytest
from fakeredis.aioredis import FakeRedis

from app.models.users import User
from app.services.otp import otp_service as otp

pytestmark = pytest.mark.unit


class _AuditRepo:
    def __init__(self):
        self.rows: list[tuple] = []

    async def daily_count(self, user_id, since):  # noqa: ARG002
        return sum(1 for u, _ in self.rows if u == user_id)

    async def phone_daily_count(self, phone, since):  # noqa: ARG002
        return sum(1 for _, p in self.rows if p == phone)

    async def add(self, user_id, phone, purpose, expires_at):  # noqa: ARG002
        self.rows.append((user_id, phone))

    async def mark_verified(self, user_id, phone):  # noqa: ARG002
        pass


def _user():
    return User(id=uuid.uuid4(), email="a@b.com", hashed_password="x", full_name="A B")


@pytest.mark.asyncio
async def test_send_then_verify_success():
    redis = FakeRedis()
    user = _user()
    res = await otp.send_otp(
        user,
        "79161234567",
        purpose="phone_verify",
        redis=redis,
        audit=_AuditRepo(),
        env="local",
    )
    assert "debug_otp" in res
    ok = await otp.verify_otp(
        user,
        "79161234567",
        res["debug_otp"],
        purpose="phone_verify",
        redis=redis,
        audit=_AuditRepo(),
    )
    assert ok is True
    assert user.phone_verified is True
    assert user.phone == "79161234567"


@pytest.mark.asyncio
async def test_per_phone_daily_cap_blocks_other_user():
    redis = FakeRedis()
    audit = _AuditRepo()
    audit.rows = [(uuid.uuid4(), "79990000000")] * 5
    with pytest.raises(otp.OtpDailyLimitError):
        await otp.send_otp(
            _user(),
            "79990000000",
            purpose="phone_verify",
            redis=redis,
            audit=audit,
            env="local",
        )


@pytest.mark.asyncio
async def test_purposes_are_isolated():
    redis = FakeRedis()
    user = _user()
    res = await otp.send_otp(
        user,
        "79161234567",
        purpose="phone_verify",
        redis=redis,
        audit=_AuditRepo(),
        env="local",
    )
    with pytest.raises(otp.OtpExpiredError):
        await otp.verify_otp(
            user,
            "79161234567",
            res["debug_otp"],
            purpose="payout_change",
            redis=redis,
            audit=_AuditRepo(),
        )


@pytest.mark.asyncio
async def test_cooldown_blocks_second_send():
    redis = FakeRedis()
    user = _user()
    await otp.send_otp(
        user, "79161234567", redis=redis, audit=_AuditRepo(), env="local"
    )
    with pytest.raises(otp.OtpCooldownError):
        await otp.send_otp(
            user, "79161234567", redis=redis, audit=_AuditRepo(), env="local"
        )


@pytest.mark.asyncio
async def test_lockout_after_three_wrong():
    redis = FakeRedis()
    user = _user()
    res = await otp.send_otp(
        user, "79161234567", redis=redis, audit=_AuditRepo(), env="local"
    )
    for _ in range(3):
        with pytest.raises(otp.OtpInvalidError):
            await otp.verify_otp(
                user, "79161234567", "000000", redis=redis, audit=_AuditRepo()
            )
    with pytest.raises(otp.OtpLockedError):
        await otp.verify_otp(
            user, "79161234567", res["debug_otp"], redis=redis, audit=_AuditRepo()
        )


@pytest.mark.asyncio
async def test_daily_cap():
    redis = FakeRedis()
    user = _user()
    full = _AuditRepo()
    full.rows = [(user.id, "y")] * 5
    with pytest.raises(otp.OtpDailyLimitError):
        await otp.send_otp(user, "79161234567", redis=redis, audit=full, env="local")


@pytest.mark.asyncio
async def test_no_debug_otp_in_production():
    redis = FakeRedis()
    res = await otp.send_otp(
        _user(), "79161234567", redis=redis, audit=_AuditRepo(), env="production"
    )
    assert "debug_otp" not in res


@pytest.mark.asyncio
async def test_send_otp_swallows_provider_unavailable(monkeypatch):
    from app.services.sms.sms_service import SmsProviderUnavailableError

    class _RaisingSms:
        async def send(self, phone, text):  # noqa: ARG002
            raise SmsProviderUnavailableError("provider down")

    monkeypatch.setattr(
        "app.services.sms.sms_service.get_sms_service", lambda: _RaisingSms()
    )

    redis = FakeRedis()
    res = await otp.send_otp(
        _user(), "79161234567", redis=redis, audit=_AuditRepo(), env="local"
    )
    assert res["sent"] is True
    assert "debug_otp" in res


@pytest.mark.asyncio
async def test_send_otp_raises_invalid_phone_on_rejected(monkeypatch):
    from app.services.sms.sms_service import SmsRejectedError

    class _RaisingSms:
        async def send(self, phone, text):  # noqa: ARG002
            raise SmsRejectedError("destination not supported")

    monkeypatch.setattr(
        "app.services.sms.sms_service.get_sms_service", lambda: _RaisingSms()
    )

    redis = FakeRedis()
    with pytest.raises(otp.OtpInvalidPhoneError):
        await otp.send_otp(
            _user(), "70000000000", redis=redis, audit=_AuditRepo(), env="local"
        )
