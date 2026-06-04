from __future__ import annotations

import hashlib
from datetime import timedelta
from unittest.mock import AsyncMock

import fakeredis.aioredis as fakeredis
import pytest

from app.core.security import create_access_token, create_refresh_token
from app.core.token_blacklist import (
    BLACKLIST_PREFIX,
    AuthBackendUnavailable,
    blacklist_auth_pair,
    blacklist_refresh_token,
    blacklist_token,
    is_token_blacklisted,
    token_key,
)

pytestmark = pytest.mark.unit


def _make_redis():
    return fakeredis.FakeRedis(decode_responses=True)


def test_token_key_uses_sha256():
    raw = "abc"
    expected_digest = hashlib.sha256(b"abc").hexdigest()
    expected_key = f"{BLACKLIST_PREFIX}{expected_digest}"

    key = token_key(raw)

    assert key == expected_key
    digest_part = key[len(BLACKLIST_PREFIX) :]
    assert len(digest_part) == 64


def test_token_key_deterministic():
    token = "some-jwt-string"
    assert token_key(token) == token_key(token)


async def test_blacklist_token_sets_with_positive_ttl():
    redis = _make_redis()
    token = create_access_token(subject="user-1")
    key = token_key(token)

    await blacklist_token(redis, token)

    ttl = await redis.ttl(key)
    assert ttl > 0


async def test_blacklist_token_uses_remaining_lifetime():
    redis = _make_redis()
    token = create_access_token(subject="user-2", expires_delta=timedelta(hours=1))
    key = token_key(token)

    await blacklist_token(redis, token)

    ttl = await redis.ttl(key)
    assert abs(ttl - 3600) <= 10


async def test_blacklist_refresh_token_uses_refresh_secret():
    redis = _make_redis()
    token = create_refresh_token(subject="user-3")
    key = token_key(token)

    await blacklist_refresh_token(redis, token)

    ttl = await redis.ttl(key)
    assert ttl > 0


async def test_blacklist_auth_pair_sets_both_keys():
    redis = _make_redis()
    access = create_access_token(subject="user-4")
    refresh = create_refresh_token(subject="user-4")

    await blacklist_auth_pair(redis, access, refresh)

    access_exists = await redis.exists(token_key(access))
    refresh_exists = await redis.exists(token_key(refresh))
    assert access_exists == 1
    assert refresh_exists == 1


async def test_is_token_blacklisted_returns_true_after_blacklist():
    redis = _make_redis()
    token = create_access_token(subject="user-5")

    await blacklist_token(redis, token)

    assert await is_token_blacklisted(redis, token) is True


async def test_is_token_blacklisted_returns_false_when_absent():
    redis = _make_redis()
    token = create_access_token(subject="user-6")

    result = await is_token_blacklisted(redis, token)

    assert result is False


async def test_is_token_blacklisted_raises_503_on_redis_failure():
    redis = _make_redis()
    token = create_access_token(subject="user-7")

    redis.exists = AsyncMock(side_effect=Exception("conn error"))

    with pytest.raises(AuthBackendUnavailable) as exc_info:
        await is_token_blacklisted(redis, token)

    assert exc_info.value.status_code == 503


async def test_blacklist_write_does_not_raise_on_redis_failure(caplog):
    redis = _make_redis()
    token = create_access_token(subject="user-8")

    redis.setex = AsyncMock(side_effect=Exception("write failure"))

    await blacklist_token(redis, token)

    assert any("blacklist" in record.message.lower() for record in caplog.records)
