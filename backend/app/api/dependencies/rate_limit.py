import logging

from fastapi import Request
from redis.exceptions import RedisError

from app.api.dependencies.auth import RedisDep
from app.core.config import settings
from app.core.rate_limit import RateLimit, check_rate_limit
from app.utils.request import get_client_ip

logger = logging.getLogger(__name__)

_PUBLIC_BROWSE_RULE = RateLimit(
    scope="public:browse:ip",
    limit=settings.PUBLIC_BROWSE_RATE_LIMIT,
    window_sec=settings.PUBLIC_BROWSE_RATE_WINDOW,
)


async def public_browse_limit(request: Request, redis: RedisDep) -> None:
    try:
        await check_rate_limit(redis, _PUBLIC_BROWSE_RULE, get_client_ip(request))
    except RedisError:
        logger.warning("public browse rate limit skipped: redis unavailable")
