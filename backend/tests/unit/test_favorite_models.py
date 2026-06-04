import pytest

from app.models.favorites import Favorite

pytestmark = pytest.mark.unit


def test_table_name_and_unique_index():
    assert Favorite.__tablename__ == "favorites"
    names = {ix.name for ix in Favorite.__table__.indexes}
    assert "uniq_favorite_user_listing" in names
    uniq = next(
        ix
        for ix in Favorite.__table__.indexes
        if ix.name == "uniq_favorite_user_listing"
    )
    assert uniq.unique is True
    assert {c.name for c in uniq.columns} == {"user_id", "listing_id"}


def test_fk_targets_cascade():
    cols = Favorite.__table__.columns
    assert next(iter(cols["user_id"].foreign_keys)).target_fullname == "users.id"
    assert next(iter(cols["listing_id"].foreign_keys)).target_fullname == "listings.id"
