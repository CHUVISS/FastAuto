from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.admin import admin_service
from app.services.admin.admin_service import get_dashboard_stats

pytestmark = pytest.mark.unit


def _result(value):
    r = MagicMock()
    r.one.return_value = value
    r.scalar_one.return_value = value
    return r


def _mock_session_factory(results):
    mock_session = AsyncMock()
    queue = list(results)

    async def _execute(_query):
        return queue.pop(0)

    mock_session.execute = _execute

    @asynccontextmanager
    async def _factory():
        yield mock_session

    return _factory


def _listing_row(total=8, active=5, reserved=2, sold=1):
    r = MagicMock()
    r.total, r.active, r.reserved, r.sold = total, active, reserved, sold
    return r


def _res_row(total=10, active=3, settling=1, completed=6):
    r = MagicMock()
    r.total = total
    r.active = active
    r.settling = settling
    r.completed = completed
    return r


@pytest.fixture
def default_results():
    return [
        _result(_listing_row()),
        _result(_res_row()),
        _result(15),
        _result(4),
    ]


async def test_get_dashboard_stats_returns_reservation_aggregates(
    monkeypatch, default_results
):
    monkeypatch.setattr(
        admin_service, "async_session_factory", _mock_session_factory(default_results)
    )
    stats = await get_dashboard_stats()
    assert stats.total_listings == 8
    assert stats.active_listings == 5
    assert stats.reserved_listings == 2
    assert stats.sold_listings == 1
    assert stats.total_reservations == 10
    assert stats.active_reservations == 3
    assert stats.settling_reservations == 1
    assert stats.completed_reservations == 6
    assert stats.total_users == 15
    assert stats.open_tickets == 4


async def test_get_dashboard_stats_no_reservations(monkeypatch, default_results):
    default_results[1] = _result(_res_row(total=0, active=0, settling=0, completed=0))
    monkeypatch.setattr(
        admin_service, "async_session_factory", _mock_session_factory(default_results)
    )
    stats = await get_dashboard_stats()
    assert stats.total_reservations == 0
    assert stats.completed_reservations == 0
