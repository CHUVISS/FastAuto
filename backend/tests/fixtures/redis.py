from __future__ import annotations

import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def redis_container():
    from testcontainers.redis import RedisContainer

    with RedisContainer("redis:7-alpine") as r:
        yield r


@pytest_asyncio.fixture
async def redis_client(redis_container):
    from redis.asyncio import Redis

    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    r = Redis(host=host, port=int(port), decode_responses=True)
    await r.flushdb()
    yield r
    await r.flushdb()
    await r.aclose()
