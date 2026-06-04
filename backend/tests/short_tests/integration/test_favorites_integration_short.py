from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.short_tests._helpers import seed_active_listing, seed_role

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_add_favorite_then_list_returns_listing(
    committed_client: AsyncClient, pg_container
):
    seller_id, _ = await seed_role(pg_container, role="user")
    user_id, headers = await seed_role(pg_container, role="user")
    listing_id = await seed_active_listing(pg_container, seller_id)

    add = await committed_client.post(
        "/api/v1/favorites", json={"listing_id": listing_id}, headers=headers
    )
    assert add.status_code == 200
    assert add.json()["added"] is True

    listed = await committed_client.get("/api/v1/favorites", headers=headers)
    assert listed.status_code == 200
    assert listing_id in [row["id"] for row in listed.json()]
