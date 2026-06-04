from datetime import date, time

import pytest

from app.services.viewings.viewing_schedule import generate_windows

pytestmark = pytest.mark.unit


def test_weekly_multiply_until_expiry():
    template = [
        {"weekday": 0, "time_from": time(10), "time_to": time(12)},
        {"weekday": 2, "time_from": time(10), "time_to": time(12)},
    ]
    slots = generate_windows(
        template, start=date(2026, 5, 25), expires=date(2026, 6, 7), repeat_weekly=True
    )
    assert len(slots) == 4
    assert all(s.window_date >= date(2026, 5, 25) for s in slots)
    assert all(s.window_date <= date(2026, 6, 7) for s in slots)


def test_no_repeat_only_first_week():
    template = [{"weekday": 0, "time_from": time(10), "time_to": time(12)}]
    slots = generate_windows(
        template, start=date(2026, 5, 25), expires=date(2026, 6, 7), repeat_weekly=False
    )
    assert len(slots) == 1


def test_never_generates_past():
    template = [{"weekday": 0, "time_from": time(10), "time_to": time(12)}]
    slots = generate_windows(
        template, start=date(2026, 5, 27), expires=date(2026, 6, 7), repeat_weekly=True
    )
    assert all(s.window_date >= date(2026, 5, 27) for s in slots)
