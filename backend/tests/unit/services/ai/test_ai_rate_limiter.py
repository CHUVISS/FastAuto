from __future__ import annotations

import pytest
from fakeredis.aioredis import FakeRedis
from fastapi import HTTPException

from app.core.config import settings
from app.services.ai.ai_rate_limiter import (
    check_ai_rate_limit,
    get_remaining_requests,
)

pytestmark = pytest.mark.unit


def _make_redis():
    return FakeRedis(decode_responses=True)


async def test_check_ai_rate_limit_passes_under_threshold():
    redis = _make_redis()
    limit = settings.AI_MAX_REQUESTS_PER_MINUTE

    for _ in range(limit):
        await check_ai_rate_limit(redis, "user-under")


async def test_check_ai_rate_limit_blocks_at_threshold():
    redis = _make_redis()
    limit = settings.AI_MAX_REQUESTS_PER_MINUTE

    for _ in range(limit):
        await check_ai_rate_limit(redis, "user-block")

    with pytest.raises(HTTPException) as exc_info:
        await check_ai_rate_limit(redis, "user-block")

    assert exc_info.value.status_code == 429


async def test_get_remaining_requests_returns_correct_count():
    redis = _make_redis()
    limit = settings.AI_MAX_REQUESTS_PER_MINUTE
    user = "user-remaining"

    m = max(1, limit - 1)
    for _ in range(m):
        await check_ai_rate_limit(redis, user)

    remaining = await get_remaining_requests(redis, user)
    assert remaining == limit - m


async def test_get_remaining_requests_never_negative():
    redis = _make_redis()
    limit = settings.AI_MAX_REQUESTS_PER_MINUTE
    user = "user-exceeded"

    for _ in range(limit):
        await check_ai_rate_limit(redis, user)

    for _ in range(3):
        with pytest.raises(HTTPException):
            await check_ai_rate_limit(redis, user)

    remaining = await get_remaining_requests(redis, user)
    assert remaining == 0
    assert remaining >= 0


async def test_check_ai_rate_limit_per_user_isolated():
    redis = _make_redis()
    limit = settings.AI_MAX_REQUESTS_PER_MINUTE

    for _ in range(limit):
        await check_ai_rate_limit(redis, "user-A")

    with pytest.raises(HTTPException):
        await check_ai_rate_limit(redis, "user-A")

    await check_ai_rate_limit(redis, "user-B")
