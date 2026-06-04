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


def test_reservation_defaults():
    s = _settings()
    assert s.RESERVATION_DEPOSIT_AMOUNT == 5000
    assert s.RESERVATION_HOLD_DAYS == 5
    assert s.DEPOSIT_PAYMENT_TTL_MINUTES == 30
    assert s.OUTCOME_PROMPT_INTERVAL_HOURS == 24
    assert s.OUTCOME_CORRECTION_HOURS == 24
    assert s.MAX_FAVORITES == 300


def test_new_scheduler_interval_defaults():
    s = _settings()
    assert s.SCHEDULER_RELEASE_EXPIRED_INTERVAL_SECONDS == 300
    assert s.SCHEDULER_FINALIZE_SETTLING_INTERVAL_SECONDS == 300
    assert s.SCHEDULER_OUTCOME_PROMPTS_INTERVAL_SECONDS == 1800
    assert s.SCHEDULER_RECONCILE_DEPOSITS_INTERVAL_SECONDS == 300


def test_anti_abuse_defaults():
    s = _settings()
    assert s.MAX_ACTIVE_RESERVATIONS_PER_BUYER == 2
    assert s.EARLY_CANCEL_WINDOW_SECONDS == 600
    assert s.EARLY_CANCEL_COOLDOWN_SECONDS == 86400
    assert s.REFUND_DELAY_WINDOW_SECONDS == 30 * 24 * 3600
    assert s.refund_delay_tiers == [0, 3600, 21600, 86400, 259200]


def test_refund_delay_tiers_parses_custom():
    s = _settings(REFUND_DELAY_TIERS_SECONDS="0,10,20")
    assert s.refund_delay_tiers == [0, 10, 20]


def test_refund_delay_tiers_rejects_negative():
    with pytest.raises(ValueError):
        _settings(REFUND_DELAY_TIERS_SECONDS="0,-1,10")


def test_hold_days_capped_at_seven():
    with pytest.raises(ValueError):
        _settings(RESERVATION_HOLD_DAYS=8)
    with pytest.raises(ValueError):
        _settings(RESERVATION_HOLD_DAYS=0)


def test_hold_days_boundaries_ok():
    assert _settings(RESERVATION_HOLD_DAYS=1).RESERVATION_HOLD_DAYS == 1
    assert _settings(RESERVATION_HOLD_DAYS=7).RESERVATION_HOLD_DAYS == 7
