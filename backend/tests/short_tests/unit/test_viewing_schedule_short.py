from __future__ import annotations

from datetime import date, time

import pytest

from app.services.viewings.viewing_schedule import generate_windows

pytestmark = pytest.mark.unit


def test_generate_windows_single_week_returns_slots_inside_range():
    template = [{"weekday": 2, "time_from": time(10, 0), "time_to": time(11, 0)}]
    slots = generate_windows(template, date(2026, 5, 25), date(2026, 5, 31), False)

    assert len(slots) == 1
    assert slots[0].time_from == time(10, 0)


def test_generate_windows_repeat_weekly_multiplies_until_expiry():
    template = [{"weekday": 2, "time_from": time(10, 0), "time_to": time(11, 0)}]
    slots = generate_windows(template, date(2026, 5, 25), date(2026, 6, 21), True)

    assert len(slots) == 4
