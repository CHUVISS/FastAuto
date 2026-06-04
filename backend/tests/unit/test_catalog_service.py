from unittest.mock import AsyncMock, patch

import pytest

from app.services.catalog import catalog_service

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_search_marks_caches_miss_then_hit():
    session = AsyncMock()
    redis = AsyncMock()
    payload = [{"id": "BMW", "name": "BMW"}]

    with (
        patch.object(
            catalog_service, "cache_get", AsyncMock(side_effect=[None, payload])
        ) as cg,
        patch.object(catalog_service, "cache_set", AsyncMock()) as cs,
        patch.object(
            catalog_service, "_search_marks_db", AsyncMock(return_value=payload)
        ) as db,
    ):
        first = await catalog_service.search_marks(session, redis, "bmw")
        second = await catalog_service.search_marks(session, redis, "bmw")

    assert first == payload
    assert second == payload
    db.assert_awaited_once()
    cs.assert_awaited_once()
    assert cg.await_count == 2


@pytest.mark.asyncio
async def test_get_modification_full_miss_then_hit():
    session = AsyncMock()
    redis = AsyncMock()
    payload = {"modification": {"id": "M1"}, "options": {"abs": True}}

    with (
        patch.object(
            catalog_service, "cache_get", AsyncMock(side_effect=[None, payload])
        ),
        patch.object(catalog_service, "cache_set", AsyncMock()) as cs,
        patch.object(
            catalog_service, "_modification_full_db", AsyncMock(return_value=payload)
        ) as db,
    ):
        first = await catalog_service.get_modification_full(session, redis, "M1")
        second = await catalog_service.get_modification_full(session, redis, "M1")

    assert first == payload
    assert second == payload
    db.assert_awaited_once()
    cs.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_modification_full_returns_none_when_missing():
    session = AsyncMock()
    redis = AsyncMock()

    with (
        patch.object(catalog_service, "cache_get", AsyncMock(return_value=None)),
        patch.object(catalog_service, "cache_set", AsyncMock()) as cs,
        patch.object(
            catalog_service, "_modification_full_db", AsyncMock(return_value=None)
        ),
    ):
        result = await catalog_service.get_modification_full(session, redis, "NOPE")

    assert result is None
    cs.assert_not_awaited()
