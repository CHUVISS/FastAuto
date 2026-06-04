from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import fakeredis.aioredis as fakeredis
import pytest

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_warm_db_pool_opens_n_connections():
    from app.core.pre_warm import warm_db_pool

    connect_count = 0

    @asynccontextmanager
    async def _mock_connect():
        nonlocal connect_count
        connect_count += 1
        conn = AsyncMock()
        conn.execute = AsyncMock()
        yield conn

    engine = MagicMock()
    engine.connect = _mock_connect

    await warm_db_pool(engine, pool_size=3)

    assert connect_count == 3


@pytest.mark.asyncio
async def test_warm_db_pool_executes_select_1():
    from app.core.pre_warm import warm_db_pool

    executed = []

    @asynccontextmanager
    async def _mock_connect():
        conn = AsyncMock()

        async def _exec(stmt):
            executed.append(str(stmt))

        conn.execute = _exec
        yield conn

    engine = MagicMock()
    engine.connect = _mock_connect

    await warm_db_pool(engine, pool_size=1)

    assert any("SELECT 1" in s or "select 1" in s.lower() for s in executed)


@pytest.mark.asyncio
async def test_warm_caches_calls_all_services():
    from app.core.pre_warm import warm_caches

    redis = fakeredis.FakeRedis(decode_responses=True)

    with (
        patch(
            "app.core.pre_warm.catalog_service.search_marks",
            new_callable=AsyncMock,
        ) as mock_marks,
        patch(
            "app.core.pre_warm.catalog_service.list_colors",
            new_callable=AsyncMock,
        ) as mock_colors,
        patch(
            "app.core.pre_warm.geo_service.list_regions",
            new_callable=AsyncMock,
        ) as mock_regions,
        patch(
            "app.core.pre_warm.geo_service.list_popular_cities",
            new_callable=AsyncMock,
        ) as mock_popular,
        patch(
            "app.core.pre_warm.geo_service.list_cities_grouped",
            new_callable=AsyncMock,
        ) as mock_grouped,
        patch("app.core.pre_warm.async_session_factory") as mock_factory,
    ):
        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        await warm_caches(redis)

    mock_marks.assert_called_once()
    mock_colors.assert_called_once()
    mock_regions.assert_called_once()
    mock_popular.assert_called_once()
    mock_grouped.assert_called_once()
