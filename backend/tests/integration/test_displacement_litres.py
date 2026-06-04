"""Engine displacement is served in litres (cc/1000, no rounding) on both the
public listing card and the listing detail's catalog specs.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from tests.short_tests._helpers import engine, seed_active_listing, seed_role

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_displacement_converted_to_litres(
    committed_client: AsyncClient, pg_container
):
    seller_id, _ = await seed_role(pg_container, role="user")
    listing_id = await seed_active_listing(pg_container, seller_id)

    # specification id must equal the listing's modification_id ('M1')
    eng = engine(pg_container)
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO catalog.specifications (id, displacement, engine_type) "
                "VALUES ('M1', '2977', 'Бензиновый') ON CONFLICT (id) DO UPDATE "
                "SET displacement = excluded.displacement"
            )
        )
    await eng.dispose()

    card = await committed_client.get("/api/v1/listings")
    row = next(r for r in card.json()["items"] if r["id"] == listing_id)
    assert row["displacement"] == "2.977"

    detail = await committed_client.get(f"/api/v1/listings/{listing_id}")
    assert detail.json()["catalog_specs"]["displacement"] == "2.977"
