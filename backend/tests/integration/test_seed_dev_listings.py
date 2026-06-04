"""End-to-end test for the dev-only listings seeder."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from scripts import seed_dev_listings as seeder
from tests.fixtures.storage import InMemoryStorage

pytestmark = pytest.mark.integration


def _mark_of(model_id: str) -> str:
    return "BMW" if model_id.startswith("BMW") else "AUDI"


async def _seed_catalog_refs(eng) -> None:
    """Seed the catalog rows the seeder needs.

    The seeder requires, for every model in ``seeder._LISTINGS``, one
    modification joined to a configuration (with ``body_type``) and a
    specification (with ``engine_type``); otherwise it bails out early
    (``dev_seed_missing_catalog_models``). It also references several colours.

    The session-scoped engine fixture already seeds colours ``black``/``white``
    and the Moscow city; the marks/models/configs/mods/specs and the remaining
    colours are added here so the seeder picks valid refs.
    """
    model_ids = sorted({spec["model_id"] for spec in seeder._LISTINGS})
    color_ids = sorted({spec["color_id"] for spec in seeder._LISTINGS})
    marks = sorted({_mark_of(mid) for mid in model_ids})

    async with eng.begin() as conn:
        for cid in color_ids:
            await conn.execute(
                text(
                    "INSERT INTO catalog.colors (id, name_ru, sort_order) "
                    "VALUES (:id, :id, 0) ON CONFLICT (id) DO NOTHING"
                ),
                {"id": cid},
            )
        for mark in marks:
            await conn.execute(
                text(
                    "INSERT INTO catalog.marks (id, name) VALUES (:id, :id) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"id": mark},
            )
        for mid in model_ids:
            mark = _mark_of(mid)
            conf_id = f"C_{mid}"
            mod_id = f"M_{mid}"
            await conn.execute(
                text(
                    "INSERT INTO catalog.models (id, mark_id, name) "
                    "VALUES (:id, :mk, :id) ON CONFLICT DO NOTHING"
                ),
                {"id": mid, "mk": mark},
            )
            await conn.execute(
                text(
                    "INSERT INTO catalog.configurations "
                    "(id, model_id, mark_id, body_type) "
                    "VALUES (:c, :m, :mk, 'SEDAN') ON CONFLICT DO NOTHING"
                ),
                {"c": conf_id, "m": mid, "mk": mark},
            )
            await conn.execute(
                text(
                    "INSERT INTO catalog.modifications "
                    "(id, mark_id, model_id, configuration_id, name) "
                    "VALUES (:mod, :mk, :m, :c, '3.0 AT') ON CONFLICT DO NOTHING"
                ),
                {"mod": mod_id, "mk": mark, "m": mid, "c": conf_id},
            )
            await conn.execute(
                text(
                    "INSERT INTO catalog.specifications (id, engine_type) "
                    "VALUES (:mod, 'Бензиновый') ON CONFLICT DO NOTHING"
                ),
                {"mod": mod_id},
            )


@pytest.mark.asyncio
async def test_seed_dev_listings_skipped_outside_local(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    await seeder.main()


@pytest.mark.asyncio
async def test_seed_dev_listings_seeds_then_idempotent(
    committed_client,  # noqa: ARG001 — wires dependency overrides + truncate
    pg_container,
    monkeypatch,
):
    monkeypatch.setattr(settings, "ENVIRONMENT", "local")
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    eng = create_async_engine(url, connect_args={"statement_cache_size": 0})

    # Point the seeder at the test engine + an in-memory image store so it
    # processes the real seed photos through Pillow without writing to disk.
    sm = async_sessionmaker(eng, expire_on_commit=False)
    storage = InMemoryStorage()
    monkeypatch.setattr(seeder, "async_session_factory", sm)
    monkeypatch.setattr(seeder, "get_image_storage", lambda: storage)

    await _seed_catalog_refs(eng)

    emails = [s["email"] for s in seeder._SELLERS]

    async def _count() -> int:
        async with eng.connect() as conn:
            return (
                await conn.execute(
                    text(
                        "SELECT count(*) FROM listings WHERE seller_id IN "
                        "(SELECT id FROM users WHERE email = ANY(:emails))"
                    ),
                    {"emails": emails},
                )
            ).scalar_one()

    await seeder.main()
    count = await _count()
    assert count == len(seeder._LISTINGS)

    # Idempotent: a second run leaves the count unchanged.
    await seeder.main()
    assert await _count() == count

    await eng.dispose()
