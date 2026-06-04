from __future__ import annotations

import os
from pathlib import Path


def _load_env_test() -> None:
    env_test = Path(__file__).resolve().parent.parent / ".env.test"
    if not env_test.exists():
        return
    for raw in env_test.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            continue
        os.environ[key.strip()] = value.strip()


def _disable_sentry() -> None:
    """Keep test-run exceptions out of the live Sentry project.

    A developer's local ``.env`` may set a real ``SENTRY_DSN``. ``Settings``
    reads that dotenv file and uses ``env_ignore_empty=True``, so the empty
    ``SENTRY_DSN`` from ``.env.test`` is ignored and the real DSN leaks in —
    ``init_sentry`` (run at ``app.main`` import) would then ship events from
    the test run. Blank it on the settings singleton before any app import.
    (No-op in CI, which has no ``.env``.)
    """
    from app.core.config import settings

    settings.SENTRY_DSN = ""


_load_env_test()
_disable_sentry()

import asyncio  # noqa: E402
from collections.abc import AsyncGenerator  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402

from tests.fixtures.committed import TRUNCATE_TABLES  # noqa: E402

pytest_plugins = [
    "tests.fixtures.db",
    "tests.fixtures.redis",
    "tests.fixtures.auth",
    "tests.fixtures.reservation",
]


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def _clear_inmem_cache():
    from app.core import inmem_cache

    inmem_cache.clear()
    yield
    inmem_cache.clear()


@pytest.fixture(autouse=True)
def _isolate_logging_state():
    """Snapshot and restore global logging state around every test.

    ``configure_logging`` (run when the app is imported) and the logging unit
    tests mutate process-global state — root handlers/level, ``logging.disable``
    and the structlog config. Without isolation, a test that reconfigures
    logging silently breaks every ``caplog`` / ``structlog.capture_logs`` based
    test that runs afterwards. This restores the prior state on teardown so no
    test can leak its logging configuration into the next.
    """
    import logging

    import structlog

    saved_structlog = structlog.get_config()
    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    saved_level = root.level
    saved_disable = logging.root.manager.disable
    try:
        yield
    finally:
        structlog.configure(**saved_structlog)
        root.handlers[:] = saved_handlers
        root.setLevel(saved_level)
        logging.disable(saved_disable)


@pytest.fixture
def mock_storage():
    from tests.fixtures.storage import InMemoryStorage

    return InMemoryStorage()


@pytest.fixture
def mock_ollama():
    from tests.fixtures.ollama import MockOllamaClient

    return MockOllamaClient()


@pytest_asyncio.fixture
async def app_with_overrides(
    engine, redis_client, mock_storage, mock_ollama, monkeypatch
):
    from app.core.db import get_session
    from app.core.redis import async_get_redis
    from app.core.storage import get_image_storage
    from app.main import app

    async def _override_session():
        conn = await engine.connect()
        trans = await conn.begin()
        try:
            async with AsyncSession(bind=conn, expire_on_commit=False) as s:
                yield s
        finally:
            await trans.rollback()
            if not conn.closed:
                await conn.close()

    async def _override_redis():
        yield redis_client

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[async_get_redis] = _override_redis
    app.dependency_overrides[get_image_storage] = lambda: mock_storage

    monkeypatch.setattr("app.services.ai.ai_service._client", mock_ollama)

    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app_with_overrides) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app_with_overrides)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def committed_client(
    pg_container,
    engine,
    redis_client,
    mock_storage,
    mock_ollama,
    monkeypatch,
):
    from app.core.db import get_session
    from app.core.redis import async_get_redis
    from app.core.storage import get_image_storage
    from app.main import app

    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})

    table_list = ", ".join(TRUNCATE_TABLES)
    truncate_sql = text(f"TRUNCATE {table_list} RESTART IDENTITY CASCADE")

    async def _truncate():
        conn = await eng.connect()
        try:
            await conn.execute(truncate_sql)
            await conn.commit()
        finally:
            await conn.close()

    await _truncate()

    async def _override_session():
        conn = await eng.connect()
        try:
            async with AsyncSession(bind=conn, expire_on_commit=False) as s:
                yield s
                await conn.commit()
        finally:
            if not conn.closed:
                await conn.close()

    async def _override_redis():
        yield redis_client

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[async_get_redis] = _override_redis
    app.dependency_overrides[get_image_storage] = lambda: mock_storage

    monkeypatch.setattr("app.services.ai.ai_service._client", mock_ollama)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    await _truncate()
    await eng.dispose()
