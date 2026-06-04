from __future__ import annotations

import uuid

import pytest_asyncio
from httpx import AsyncClient

from tests.fixtures.committed import seed_user


@pytest_asyncio.fixture
async def manager_headers(committed_client: AsyncClient, pg_container, engine):
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.core.security import create_access_token

    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    user_id = await seed_user(eng, "manager", f"mgr_{uuid.uuid4().hex[:6]}@example.org")
    await eng.dispose()
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(committed_client: AsyncClient, pg_container, engine):
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.core.security import create_access_token

    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    user_id = await seed_user(eng, "admin", f"adm_{uuid.uuid4().hex[:6]}@example.org")
    await eng.dispose()
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}
