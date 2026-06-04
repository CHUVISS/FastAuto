from __future__ import annotations

from datetime import date


def user_auth_key(user_id: str) -> str:
    return f"user:auth:{user_id}"


def admin_stats_key(date_from: date | None, date_to: date | None) -> str:
    return f"admin:stats:{date_from}:{date_to}"


TTL_USER_AUTH = 60
TTL_ADMIN_STATS = 30
