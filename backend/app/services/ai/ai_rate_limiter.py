from __future__ import annotations

import time

from redis.asyncio import Redis

from app.core.config import settings
from app.core.rate_limit import RateLimit, check_rate_limit

_AI_RULE = RateLimit(
    scope="ai:chat",
    limit=settings.AI_MAX_REQUESTS_PER_MINUTE,
    window_sec=settings.AI_RATE_LIMIT_WINDOW_SEC,
)


async def check_ai_rate_limit(redis: Redis, user_id: str) -> None:
    await check_rate_limit(redis, _AI_RULE, user_id)


async def get_remaining_requests(redis: Redis, user_id: str) -> int:
    key = f"rl:{_AI_RULE.scope}:{user_id}"
    window_start = time.time() - _AI_RULE.window_sec
    await redis.zremrangebyscore(key, "-inf", window_start)
    used = int(await redis.zcard(key))
    return max(0, _AI_RULE.limit - used)
