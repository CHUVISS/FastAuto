from __future__ import annotations

from datetime import date

import pytest

from app.core.cache_keys import (
    TTL_ADMIN_STATS,
    TTL_USER_AUTH,
    admin_stats_key,
    user_auth_key,
)

pytestmark = pytest.mark.unit


def test_user_auth_key_format():
    assert user_auth_key("uid") == "user:auth:uid"


def test_admin_stats_key_with_dates():
    key = admin_stats_key(date(2026, 1, 1), date(2026, 12, 31))
    assert key == "admin:stats:2026-01-01:2026-12-31"


def test_admin_stats_key_with_none_dates():
    assert admin_stats_key(None, None) == "admin:stats:None:None"


def test_ttl_constants_positive():
    for ttl in (TTL_USER_AUTH, TTL_ADMIN_STATS):
        assert ttl > 0
