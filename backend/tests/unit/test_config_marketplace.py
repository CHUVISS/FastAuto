import pytest

from app.core.config import Settings

pytestmark = pytest.mark.unit

_SAFE = "a_secure_key_not_in_insecure_set_1234"


def _settings(**over):
    return Settings(
        _env_file=None,
        **{
            "SECRET_KEY": _SAFE,
            "REFRESH_SECRET_KEY": _SAFE,
            "FIRST_SUPERUSER_PASSWORD": _SAFE,
            "MINIO_ACCESS_KEY": _SAFE,
            "MINIO_SECRET_KEY": _SAFE,
            **over,
        },
    )


def test_listing_and_reservation_defaults():
    s = _settings()
    assert s.MAX_ACTIVE_LISTINGS == 5
    assert s.LISTING_LIFETIME_DAYS == 30
    assert s.RESERVATION_HOLD_DAYS == 5
    assert not hasattr(s, "FEE_PERCENT")
    assert not hasattr(s, "MIN_COMMISSION")
    assert not hasattr(s, "MAX_PAYOUT_METHODS")
    assert not hasattr(s, "DEPOSIT_PERCENT")


def test_sms_backend_default_is_fake():
    assert _settings().SMS_BACKEND == "fake"


def test_otp_defaults():
    s = _settings()
    assert s.OTP_TTL_SECONDS == 600
    assert s.OTP_COOLDOWN_SECONDS == 60
    assert s.OTP_LOCKOUT_SECONDS == 900
    assert s.OTP_MAX_ATTEMPTS == 3
    assert s.OTP_MAX_DAILY == 5


def test_scheduler_and_browse_defaults():
    s = _settings()
    assert s.SCHEDULER_ENABLED is True
    assert s.SCHEDULER_EXPIRE_LISTINGS_INTERVAL_SECONDS == 3600
    assert s.PUBLIC_BROWSE_RATE_LIMIT == 120
    assert s.PUBLIC_BROWSE_RATE_WINDOW == 60
    assert not hasattr(s, "SCHEDULER_AUTOCANCEL_INTERVAL_SECONDS")
    assert not hasattr(s, "SCHEDULER_RETRY_PAYOUTS_INTERVAL_SECONDS")


def test_yookassa_and_exolve_fields_exist():
    s = _settings()
    assert s.YOOKASSA_SHOP_ID == ""
    assert s.YOOKASSA_SECRET_KEY == ""
    assert s.YOOKASSA_RETURN_URL.startswith("http")
    assert s.EXOLVE_BASE_URL == "https://api.exolve.ru"
