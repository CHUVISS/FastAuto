from __future__ import annotations

import pytest

import app.core.redis as redis_module
from app.core.redis import (
    async_get_redis,
    build_url,
    close_redis_pool,
    create_redis_pool,
    get_redis_client,
)

pytestmark = pytest.mark.unit


def _reset_pool(monkeypatch):
    monkeypatch.setattr(redis_module, "_pool", None)


def test_build_url_without_password(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        redis_module,
        "settings",
        SimpleNamespace(
            REDIS_USE_TLS=False,
            REDIS_PASSWORD=None,
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_DB=0,
        ),
    )
    url = build_url()
    assert url == "redis://localhost:6379/0"


def test_build_url_with_password(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        redis_module,
        "settings",
        SimpleNamespace(
            REDIS_USE_TLS=False,
            REDIS_PASSWORD="testpwd",
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_DB=0,
        ),
    )
    url = build_url()
    assert ":testpwd@" in url


def test_build_url_uses_rediss_when_tls(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        redis_module,
        "settings",
        SimpleNamespace(
            REDIS_USE_TLS=True,
            REDIS_PASSWORD=None,
            REDIS_HOST="localhost",
            REDIS_PORT=6380,
            REDIS_DB=0,
        ),
    )
    url = build_url()
    assert url.startswith("rediss://")


def test_create_pool_initializes_singleton(monkeypatch):
    _reset_pool(monkeypatch)
    pool = create_redis_pool()
    try:
        assert redis_module._pool is not None
        assert pool is redis_module._pool
    finally:
        monkeypatch.setattr(redis_module, "_pool", None)


def test_get_redis_client_raises_when_pool_not_initialized(monkeypatch):
    _reset_pool(monkeypatch)
    with pytest.raises(RuntimeError):
        get_redis_client()


async def test_close_pool_resets_singleton(monkeypatch):
    _reset_pool(monkeypatch)
    create_redis_pool()
    assert redis_module._pool is not None

    await close_redis_pool()

    assert redis_module._pool is None


async def test_async_get_redis_yields_and_closes(monkeypatch):
    _reset_pool(monkeypatch)
    create_redis_pool()
    try:
        async for client in async_get_redis():
            assert client is not None
    finally:
        await close_redis_pool()
