from __future__ import annotations

import logging
import secrets
import time
from dataclasses import dataclass

from fastapi import HTTPException, status
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimit:
    scope: str
    limit: int
    window_sec: int


async def check_rate_limit(redis: Redis, rule: RateLimit, identity: str) -> None:
    key = f"rl:{rule.scope}:{identity}"
    now = time.time()
    window_start = now - rule.window_sec
    key_ttl = rule.window_sec + 10

    member = f"{now}:{secrets.token_hex(4)}"

    pipe = redis.pipeline()
    await pipe.zremrangebyscore(key, "-inf", window_start)
    await pipe.zadd(key, {member: now})
    await pipe.zcard(key)
    await pipe.expire(key, key_ttl)
    results = await pipe.execute()

    count: int = results[2]

    if count > rule.limit:
        await redis.zrem(key, member)
        logger.warning(
            "Rate limit exceeded: scope=%s identity=%s count=%d limit=%d",
            rule.scope,
            identity,
            count,
            rule.limit,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Try again in {rule.window_sec} seconds.",
            headers={"Retry-After": str(rule.window_sec)},
        )
