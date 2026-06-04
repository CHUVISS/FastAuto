from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.db import async_session_factory
from app.services.catalog import catalog_service
from app.services.geo import geo_service

log = structlog.get_logger(__name__)


async def warm_db_pool(engine: AsyncEngine, pool_size: int) -> None:
    async def _conn() -> None:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    await asyncio.gather(*(_conn() for _ in range(pool_size)))


async def warm_caches(redis: Redis) -> None:
    async def _s(work: Callable[[AsyncSession], Awaitable[Any]]) -> Any:
        async with async_session_factory() as session:
            return await work(session)

    await asyncio.gather(
        _s(lambda s: catalog_service.search_marks(s, redis, "")),
        _s(lambda s: catalog_service.list_colors(s, redis)),
        _s(lambda s: geo_service.list_regions(s, redis)),
        _s(lambda s: geo_service.list_popular_cities(s, redis)),
        _s(lambda s: geo_service.list_cities_grouped(s, redis)),
    )


async def run_pre_warm(engine: AsyncEngine, pool_size: int, redis: Redis) -> None:
    try:
        await warm_db_pool(engine, pool_size)
        log.info("db_pool_warmed", connections=pool_size)
    except Exception as exc:
        log.warning("db_pool_warmup_skipped", reason=str(exc))

    try:
        await warm_caches(redis)
        log.info("cache_prewarmed", sources=["catalog", "geo"])
    except Exception as exc:
        log.warning("cache_prewarm_skipped", reason=str(exc))
