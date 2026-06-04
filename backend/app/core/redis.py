from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_pool: aioredis.ConnectionPool | None = None


def build_url() -> str:
    scheme = "rediss" if settings.REDIS_USE_TLS else "redis"
    auth = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
    return f"{scheme}://{auth}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


def create_redis_pool() -> aioredis.ConnectionPool:
    global _pool
    _pool = aioredis.ConnectionPool.from_url(
        build_url(),
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        decode_responses=True,
    )
    logger.info(
        "Redis pool created (%s:%s/%s, max_conn=%d)",
        settings.REDIS_HOST,
        settings.REDIS_PORT,
        settings.REDIS_DB,
        settings.REDIS_MAX_CONNECTIONS,
    )
    return _pool


async def close_redis_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None
        logger.info("Redis pool closed")


def get_redis_client() -> Redis:
    if _pool is None:
        raise RuntimeError(
            "Redis pool не инициализирован. Вызовите create_redis_pool() при старте."
        )
    return aioredis.Redis(connection_pool=_pool)


async def async_get_redis() -> AsyncGenerator[Redis, None]:
    client = get_redis_client()
    try:
        yield client
    finally:
        await client.aclose()
