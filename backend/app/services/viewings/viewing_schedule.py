from datetime import date, timedelta
from typing import Any

from app.models.listings import ViewingWindow


def generate_windows(
    template: list[dict[str, Any]],
    start: date,
    expires: date,
    repeat_weekly: bool,
) -> list[ViewingWindow]:
    windows: list[ViewingWindow] = []
    week_start = start - timedelta(days=start.weekday())
    cur = week_start
    while cur <= expires:
        for entry in template:
            slot_date = cur + timedelta(days=int(entry["weekday"]))
            if start <= slot_date <= expires:
                windows.append(
                    ViewingWindow(
                        window_date=slot_date,
                        time_from=entry["time_from"],
                        time_to=entry["time_to"],
                    )
                )
        if not repeat_weekly:
            break
        cur += timedelta(days=7)
    return windows
