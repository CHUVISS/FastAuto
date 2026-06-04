import pytest

from app.models.listings import Condition, Listing, ListingImage, ListingStatus

pytestmark = pytest.mark.unit


def test_listing_status_values():
    assert {s.value for s in ListingStatus} == {
        "draft",
        "pending_review",
        "active",
        "reserved",
        "sold",
        "archived",
    }


def test_condition_values():
    assert {c.value for c in Condition} == {"excellent", "good", "fair", "poor"}


def test_listing_defaults_and_fk():
    cols = Listing.__table__.columns
    assert cols["status"].default.arg == ListingStatus.draft
    assert cols["license_plate_edit_count"].default.arg == 0
    assert cols["viewing_repeat_weekly"].default.arg is False
    fk = next(iter(cols["modification_id"].foreign_keys))
    assert fk.target_fullname == "catalog.modifications.id"
    assert "payout_method_id" not in cols


def test_listing_has_denormalized_facets():
    cols = set(Listing.__table__.columns.keys())
    assert {"mark_id", "model_id", "body_type", "engine_type"} <= cols


def test_listing_partial_search_indexes():
    index_names = {ix.name for ix in Listing.__table__.indexes}
    assert {
        "idx_listings_seller",
        "uniq_active_vin",
        "idx_active_recency",
        "idx_active_mark_recency",
        "idx_active_model_recency",
        "idx_active_price",
        "idx_active_mark_price",
        "idx_active_model_price",
    } <= index_names


def test_listing_image_partial_unique_primary():
    index_names = {ix.name for ix in ListingImage.__table__.indexes}
    assert "uniq_primary_image" in index_names
