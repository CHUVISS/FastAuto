import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

pytestmark = pytest.mark.integration


async def _seed(pg_container):
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO catalog.marks (id, name, cyrillic_name, popular, country) "
                "VALUES ('BMW', 'BMW', 'БМВ', true, 'Germany') "
                "ON CONFLICT (id) DO NOTHING"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO catalog.modifications "
                "(id, mark_id, model_id, generation_id, configuration_id, name) "
                "VALUES ('MOD1', 'BMW', 'BMW_5', 'G1', 'C1', '3.0 AT') "
                "ON CONFLICT (id) DO NOTHING"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO catalog.specifications (id, power) VALUES ('MOD1', '249') "
                "ON CONFLICT (id) DO NOTHING"
            )
        )
    await eng.dispose()


@pytest.mark.asyncio
async def test_marks_endpoint_public(committed_client: AsyncClient, pg_container):
    await _seed(pg_container)
    resp = await committed_client.get("/api/v1/catalog/marks", params={"q": "bmw"})
    assert resp.status_code == 200
    assert any(m["id"] == "BMW" for m in resp.json())


@pytest.mark.asyncio
async def test_modification_full_endpoint(committed_client: AsyncClient, pg_container):
    await _seed(pg_container)
    resp = await committed_client.get("/api/v1/catalog/modifications/MOD1")
    assert resp.status_code == 200
    assert resp.json()["specification"]["power"] == "249"


@pytest.mark.asyncio
async def test_modification_full_404(committed_client: AsyncClient):
    resp = await committed_client.get("/api/v1/catalog/modifications/NOPE")
    assert resp.status_code == 404
