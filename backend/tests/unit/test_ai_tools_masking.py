import json
import uuid
from unittest.mock import AsyncMock

import pytest

from app.models.listings import Condition, Listing, ListingStatus
from app.services.ai import ai_tools

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_get_listing_details_masks_vin():
    listing_id = uuid.uuid4()
    listing = Listing(
        id=listing_id,
        seller_id=uuid.uuid4(),
        modification_id="M1",
        mark_id="BMW",
        model_id="BMW_5",
        year=2019,
        price=2_500_000,
        mileage=1000,
        color_id="black",
        condition=Condition.good,
        city_id="7700000000000",
        vin="WVWZZZ1KZ6W123456",
        status=ListingStatus.active,
    )
    session = AsyncMock()
    session.get = AsyncMock(return_value=listing)

    raw = await ai_tools._db_get_listing_details(
        session, {"listing_id": str(listing_id)}
    )
    payload = json.loads(raw)
    assert payload["vin"] == "***************56"
    assert "WVWZZZ1KZ6W123456" not in raw
