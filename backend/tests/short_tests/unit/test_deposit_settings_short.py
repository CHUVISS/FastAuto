from __future__ import annotations

import pytest

from app.core.config import Settings

pytestmark = [
    pytest.mark.unit,
    pytest.mark.filterwarnings("ignore::UserWarning"),
]


def _settings(**over):
    return Settings(_env_file=None, **over)


def test_deposit_defaults_present_and_consistent(monkeypatch):
    # Settings still reads os.environ even with _env_file=None; CI sets these
    # to non-default values, so clear them to assert the code defaults.
    for var in (
        "SECRET_KEY",
        "REFRESH_SECRET_KEY",
        "FIRST_SUPERUSER_PASSWORD",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
    ):
        monkeypatch.delenv(var, raising=False)
    s = _settings()

    assert s.RESERVATION_DEPOSIT_AMOUNT == 5000
    assert s.OUTCOME_CORRECTION_HOURS == 24
    assert s.MAX_FAVORITES == 300
    assert s.MINIO_ACCESS_KEY == "minioadmin"
    assert s.MINIO_SECRET_KEY == "minioadmin"
    assert s.REFRESH_SECRET_KEY == "changethis"
    assert s.FIRST_SUPERUSER_PASSWORD == "changethis"
    assert s.SECRET_KEY == "changethis"


def test_hold_days_outside_bank_cap_throws():
    with pytest.raises(ValueError, match="1..7"):
        _settings(RESERVATION_HOLD_DAYS=8)
    with pytest.raises(ValueError, match="1..7"):
        _settings(RESERVATION_HOLD_DAYS=0)
