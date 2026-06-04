from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import fakeredis.aioredis as fakeredis
import pytest
from redis.exceptions import RedisError

from app.core.cache import (
    cache_delete,
    cache_delete_pattern,
    cache_get,
    cache_get_response,
    cache_set,
    cache_set_response,
)

pytestmark = pytest.mark.unit


def _make_redis():
    return fakeredis.FakeRedis(decode_responses=True)


def _enabled_settings():
    return SimpleNamespace(CACHE_ENABLED=True)


def _disabled_settings():
    return SimpleNamespace(CACHE_ENABLED=False)


async def test_cache_get_returns_none_when_disabled(monkeypatch):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _disabled_settings())
    await redis.set("key:disabled", '{"x": 1}')

    result = await cache_get(redis, "key:disabled")

    assert result is None


async def test_cache_get_returns_dict_after_set(monkeypatch):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _enabled_settings())
    payload = {"id": 42, "name": "test"}

    await cache_set(redis, "key:roundtrip", payload, ttl=60)
    result = await cache_get(redis, "key:roundtrip")

    assert result == payload


async def test_cache_get_returns_none_on_redis_failure(monkeypatch):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _enabled_settings())
    redis.get = AsyncMock(side_effect=RedisError("connection refused"))

    result = await cache_get(redis, "key:failure")

    assert result is None


async def test_cache_get_returns_none_on_corrupted_json(monkeypatch):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _enabled_settings())
    await redis.set("key:corrupt", "junk bytes {{{{")

    result = await cache_get(redis, "key:corrupt")

    assert result is None


async def test_cache_set_uses_orjson_serialization(monkeypatch):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _enabled_settings())
    uid = uuid.uuid4()
    dt = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
    payload = {"uid": str(uid), "dt": dt.isoformat()}

    await cache_set(redis, "key:orjson", payload, ttl=60)
    result = await cache_get(redis, "key:orjson")

    assert result is not None
    assert result["uid"] == str(uid)
    assert result["dt"] == dt.isoformat()


async def test_cache_set_respects_ttl(monkeypatch):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _enabled_settings())

    await cache_set(redis, "key:ttl", {"v": 1}, ttl=10)
    pttl = await redis.pttl("key:ttl")

    assert 0 < pttl <= 10_000


async def test_cache_set_disabled_does_not_write(monkeypatch):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _disabled_settings())
    await cache_set(redis, "key:no_write", {"secret": True}, ttl=60)

    monkeypatch.setattr("app.core.cache.settings", _enabled_settings())
    result = await cache_get(redis, "key:no_write")

    assert result is None


async def test_cache_get_response_returns_response_object(monkeypatch):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _enabled_settings())
    json_str = '{"status": "ok"}'

    await cache_set_response(redis, "key:resp", json_str, ttl=60)
    response = await cache_get_response(redis, "key:resp")

    assert response is not None
    assert response.media_type == "application/json"


async def test_cache_get_response_returns_none_when_not_found(monkeypatch):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _enabled_settings())

    result = await cache_get_response(redis, "key:missing_response")

    assert result is None


async def test_cache_set_response_returns_response_and_caches(monkeypatch):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _enabled_settings())
    json_str = '{"cars": []}'

    response = await cache_set_response(redis, "key:set_resp", json_str, ttl=60)

    assert response is not None
    assert response.media_type == "application/json"

    cached = await cache_get_response(redis, "key:set_resp")
    assert cached is not None


async def test_cache_delete_removes_keys(monkeypatch):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _enabled_settings())
    await cache_set(redis, "key:del1", {"a": 1}, ttl=60)
    await cache_set(redis, "key:del2", {"b": 2}, ttl=60)

    await cache_delete(redis, "key:del1", "key:del2")

    assert await cache_get(redis, "key:del1") is None
    assert await cache_get(redis, "key:del2") is None


async def test_cache_delete_pattern_uses_scan_iter(monkeypatch):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _enabled_settings())
    for i in range(5):
        await redis.set(f"test:{i}", f"value{i}")

    await cache_delete_pattern(redis, "test:*")

    for i in range(5):
        exists = await redis.exists(f"test:{i}")
        assert exists == 0


async def test_cache_delete_pattern_handles_empty_match(monkeypatch):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _enabled_settings())

    await cache_delete_pattern(redis, "nonexistent:pattern:*")


async def test_cache_delete_pattern_swallows_errors(monkeypatch, caplog):
    redis = _make_redis()
    monkeypatch.setattr("app.core.cache.settings", _enabled_settings())

    async def _failing_scan_iter(*_args, **_kwargs):
        raise RedisError("scan error")
        # noinspection PyUnreachableCode
        yield

    redis.scan_iter = _failing_scan_iter

    await cache_delete_pattern(redis, "test:*")

    assert any("pattern" in record.message.lower() for record in caplog.records)
