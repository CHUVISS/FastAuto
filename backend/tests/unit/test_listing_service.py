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
        "mileage": 85000,
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


def test_vin_immutable_after_first_save():
    listing = _listing()
    with pytest.raises(svc.ImmutableFieldError):
        svc.apply_edit(listing, {"vin": "OTHER1234567890XY"})


def test_license_plate_max_one_edit():
    listing = _listing(license_plate="A123AA77", license_plate_edit_count=1)
    with pytest.raises(svc.ImmutableFieldError):
        svc.apply_edit(listing, {"license_plate": "B456BB99"})


def test_city_locked_after_publish():
    listing = _listing(status=ListingStatus.active, published_at=datetime.now())
    with pytest.raises(svc.ImmutableFieldError):
        svc.apply_edit(listing, {"city_id": "1600000100000"})


def test_price_always_editable_even_when_active():
    listing = _listing(status=ListingStatus.active, published_at=datetime.now())
    svc.apply_edit(listing, {"price": 2_400_000})
    assert listing.price == 2_400_000


def test_non_price_field_locked_when_not_draft():
    listing = _listing(status=ListingStatus.active, published_at=datetime.now())
    with pytest.raises(svc.ImmutableFieldError):
        svc.apply_edit(listing, {"mileage": 90000})


def test_pending_review_also_locks_non_price_fields():
    listing = _listing(status=ListingStatus.pending_review)
    with pytest.raises(svc.ImmutableFieldError):
        svc.apply_edit(listing, {"mileage": 90000})


def test_sale_address_and_payment_prefs_editable_when_active():
    listing = _listing(status=ListingStatus.active, published_at=datetime.now())
    svc.apply_edit(
        listing,
        {
            "sale_address": "Казань, ул. Новая, 2",
            "accepts_cash": False,
            "accepts_transfer": True,
        },
    )
    assert listing.sale_address == "Казань, ул. Новая, 2"
    assert listing.accepts_cash is False
    assert listing.accepts_transfer is True


def test_publish_requires_image():
    with pytest.raises(svc.PublishValidationError):
        svc.validate_publish(_listing(), image_count=0, window_count=1)


def test_publish_requires_window_when_viewing_enabled():
    listing = _listing(viewing_enabled=True)
    with pytest.raises(svc.PublishValidationError):
        svc.validate_publish(listing, image_count=1, window_count=0)


def test_publish_requires_sale_address_when_viewing_enabled():
    listing = _listing(viewing_enabled=True, sale_address=None)
    with pytest.raises(svc.PublishValidationError):
        svc.validate_publish(listing, image_count=1, window_count=1)


def test_publish_requires_a_payment_preference():
    listing = _listing(accepts_cash=False, accepts_transfer=False)
    with pytest.raises(svc.PublishValidationError):
        svc.validate_publish(listing, image_count=1, window_count=1)


def test_publish_ok_sets_pending_review():
    listing = _listing()
    svc.do_publish(listing, image_count=2, window_count=1)
    assert listing.status == ListingStatus.pending_review


def test_max_active_limit():
    with pytest.raises(svc.MaxActiveListingsError):
        svc.assert_can_create(active_count=5, max_active=5)


@pytest.mark.parametrize(
    "year,ok", [(2016, True), (2025, True), (2015, False), (2026, False)]
)
def test_year_within_generation_range(year, ok):
    if ok:
        svc.validate_year(year, gen_from=2016, gen_to=2023)
    else:
        with pytest.raises(svc.PublishValidationError):
            svc.validate_year(year, gen_from=2016, gen_to=2023)
