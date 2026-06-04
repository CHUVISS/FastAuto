from __future__ import annotations

import pytest

from app.models.favorites import Favorite

pytestmark = pytest.mark.unit


def test_unique_user_listing_index_exists():
    names = {ix.name for ix in Favorite.__table__.indexes}
    assert "uniq_favorite_user_listing" in names
    uniq = next(
        ix
        for ix in Favorite.__table__.indexes
        if ix.name == "uniq_favorite_user_listing"
    )
    assert uniq.unique is True


def test_listing_fk_uses_cascade():
    cols = Favorite.__table__.columns
    listing_fk = next(iter(cols["listing_id"].foreign_keys))
    assert listing_fk.target_fullname == "listings.id"
    assert listing_fk.ondelete == "CASCADE"
