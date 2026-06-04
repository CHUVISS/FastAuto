from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from app.models.listings import Condition, Listing, ListingStatus
from app.services.listings import listing_service as svc

pytestmark = pytest.mark.unit


def _listing(**over):
    base = {
        "id": uuid.uuid4(),
        "seller_id": uuid.uuid4(),
        "modification_id": "M1",
        "mark_id": "BMW",
        "model_id": "BMW_5",
        "year": 2019,
        "price": 2_500_000,
        "mileage": 85_000,
        "color_id": "black",
        "condition": Condition.good,
        "city_id": "7700000000000",
        "vin": "WBA12345678901234",
        "sale_address": "Москва, ул. Пример, 1",
        "accepts_cash": True,
        "status": ListingStatus.draft,
    }
    base.update(over)
    return Listing(**base)


def test_apply_edit_vin_immutable_throws():
    listing = _listing()
    with pytest.raises(svc.ImmutableFieldError):
        svc.apply_edit(listing, {"vin": "OTHER123456789012"})


def test_validate_publish_requires_sale_address_when_viewing_enabled():
    listing = _listing(viewing_enabled=True, sale_address=None)
    with pytest.raises(svc.PublishValidationError, match="Sale address"):
        svc.validate_publish(listing, image_count=1, window_count=1)


def test_validate_year_outside_generation_throws():
    with pytest.raises(svc.PublishValidationError):
        svc.validate_year(2030, gen_from=2016, gen_to=2023)
    # also: edits to price are allowed even after publish
    listing = _listing(status=ListingStatus.active, published_at=datetime.now())
    svc.apply_edit(listing, {"price": 2_400_000})
    assert listing.price == 2_400_000
