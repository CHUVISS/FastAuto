from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.short_tests._helpers import seed_active_listing, seed_role

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_public_list_returns_active_listings_with_masked_vin(
    committed_client: AsyncClient, pg_container
):
    seller_id, _ = await seed_role(pg_container, role="user")
    await seed_active_listing(pg_container, seller_id)

    response = await committed_client.get("/api/v1/listings")

    assert response.status_code == 200
    items = response.json()["items"]
    assert items, "active listing should appear in the public list"
    for row in items:
        if row.get("vin") is not None:
            assert row["vin"].startswith("*"), "vin must be masked"
