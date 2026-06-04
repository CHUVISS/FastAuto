from __future__ import annotations

import pytest
from fakeredis.aioredis import FakeRedis
from fastapi import HTTPException
from freezegun import freeze_time

from app.core.rate_limit import RateLimit, check_rate_limit

pytestmark = pytest.mark.unit


def _make_redis():
    return FakeRedis(decode_responses=True)


def _make_rule(scope="test", limit=5, window_sec=60):
    return RateLimit(scope=scope, limit=limit, window_sec=window_sec)


async def test_rate_limit_passes_under_threshold():
    redis = _make_redis()
    rule = _make_rule(limit=5)

    for _ in range(5):
        await check_rate_limit(redis, rule, "user1")


async def test_rate_limit_raises_429_at_threshold_exceed():
    redis = _make_redis()
    rule = _make_rule(limit=3)

    for _ in range(3):
        await check_rate_limit(redis, rule, "user2")

    with pytest.raises(HTTPException) as exc_info:
        await check_rate_limit(redis, rule, "user2")

    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers


async def test_rate_limit_window_slides():
    redis = _make_redis()
    rule = _make_rule(limit=5, window_sec=60)
    identity = "user3"

    with freeze_time("2025-01-01 12:00:00"):
        for _ in range(5):
            await check_rate_limit(redis, rule, identity)

    with freeze_time("2025-01-01 12:01:01"):
        await check_rate_limit(redis, rule, identity)


async def test_rate_limit_per_identity_isolated():
    redis = _make_redis()
    rule = _make_rule(limit=3)

    for _ in range(3):
        await check_rate_limit(redis, rule, "a")

    await check_rate_limit(redis, rule, "b")


async def test_rate_limit_pipelines_zset_ops():
    redis = _make_redis()
    rule = _make_rule(scope="zset_test", limit=5)
    identity = "user5"

    await check_rate_limit(redis, rule, identity)

    key = f"rl:{rule.scope}:{identity}"
    card = await redis.zcard(key)
    assert card == 1


async def test_rate_limit_key_format():
    redis = _make_redis()
    rule = _make_rule(scope="test", limit=5)
    identity = "user1"

    await check_rate_limit(redis, rule, identity)

    exists = await redis.exists(f"rl:{rule.scope}:{identity}")
    assert exists == 1


async def test_rate_limit_retry_after_header_matches_window():
    redis = _make_redis()
    rule = _make_rule(limit=1, window_sec=120)
    identity = "user7"

    await check_rate_limit(redis, rule, identity)

    with pytest.raises(HTTPException) as exc_info:
        await check_rate_limit(redis, rule, identity)

    assert exc_info.value.headers["Retry-After"] == str(rule.window_sec)
