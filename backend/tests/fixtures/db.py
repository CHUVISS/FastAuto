from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

import app.models.ai  # noqa: F401
import app.models.catalog  # noqa: F401
import app.models.favorites  # noqa: F401
import app.models.geo  # noqa: F401
import app.models.listings  # noqa: F401
import app.models.notifications  # noqa: F401
import app.models.payout  # noqa: F401
import app.models.reservations  # noqa: F401
import app.models.tickets  # noqa: F401
import app.models.users  # noqa: F401


@pytest.fixture(scope="session")
def pg_container():
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:17-alpine") as pg:
        yield pg


@pytest_asyncio.fixture(scope="session")
async def engine(pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    async with eng.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS catalog"))
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS geo"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(
            text(
                "INSERT INTO catalog.colors (id, name_ru, sort_order) VALUES "
                "('black', 'Чёрный', 10), "
                "('white', 'Белый', 20), "
                "('other', 'Другой', 999) "
                "ON CONFLICT (id) DO NOTHING"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO geo.regions "
                "(id, code, iso_code, name_ru, fullname_ru, type_) VALUES "
                "('7700000000000', '77', 'RU-MOW', 'Москва', 'Москва', 'Город') "
                "ON CONFLICT (id) DO NOTHING"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO geo.cities "
                "(id, region_id, name_ru, type_, is_capital, is_popular) VALUES "
                "('7700000000000', '7700000000000', 'Москва', 'Город', true, true), "
                "('1600000100000', '7700000000000', 'Казань', 'Город', false, false) "
                "ON CONFLICT (id) DO NOTHING"
            )
        )
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(pg_container, engine) -> AsyncGenerator[AsyncSession, None]:  # noqa: ARG001
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    conn = await eng.connect()
    trans = await conn.begin()
    try:
        async with AsyncSession(bind=conn, expire_on_commit=False) as session:
            yield session
    finally:
        await trans.rollback()
        await conn.close()
    await eng.dispose()
