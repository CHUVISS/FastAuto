from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import (
    apply_partial_update,
    flush_refresh,
    get_by_pk,
    reset_primary_flag,
)
from app.models.listings import Condition, Listing, ListingImage
from app.models.users import User

pytestmark = pytest.mark.integration


def _user(**kw) -> User:
    defaults = {
        "full_name": "Base Test",
        "email": f"base_{uuid.uuid4().hex[:8]}@example.com",
        "hashed_password": "x",
    }
    defaults.update(kw)
    return User(**defaults)


async def _listing(db_session: AsyncSession) -> Listing:
    seller = _user()
    db_session.add(seller)
    await db_session.flush()
    await db_session.execute(
        text(
            "INSERT INTO catalog.modifications (id) VALUES ('M1') ON CONFLICT DO NOTHING"
        )
    )
    listing = Listing(
        seller_id=seller.id,
        modification_id="M1",
        mark_id="BMW",
        model_id="BMW_5",
        year=2020,
        price=2_500_000,
        mileage=1000,
        color_id="black",
        condition=Condition.good,
        city_id="7700000000000",
    )
    db_session.add(listing)
    await db_session.flush()
    return listing


async def test_get_by_pk_returns_existing(db_session: AsyncSession):
    user = _user()
    db_session.add(user)
    await db_session.flush()
    found = await get_by_pk(db_session, User, user.id)
    assert found is not None
    assert found.id == user.id


async def test_get_by_pk_returns_none_for_missing(db_session: AsyncSession):
    result = await get_by_pk(db_session, User, uuid.uuid4())
    assert result is None


async def test_flush_refresh_returns_instance(db_session: AsyncSession):
    user = _user()
    db_session.add(user)
    refreshed = await flush_refresh(db_session, user)
    assert refreshed is user
    assert refreshed.id is not None


async def test_apply_partial_update_changes_fields(db_session: AsyncSession):
    user = _user()
    db_session.add(user)
    await db_session.flush()
    updated = await apply_partial_update(
        db_session, user, {"full_name": "Updated", "phone": "79990000001"}
    )
    assert updated.full_name == "Updated"
    assert updated.phone == "79990000001"


async def test_apply_partial_update_ignores_missing_keys(db_session: AsyncSession):
    user = _user(full_name="Original")
    db_session.add(user)
    await db_session.flush()
    original = user.full_name
    updated = await apply_partial_update(db_session, user, {"phone": "79990000002"})
    assert updated.full_name == original


async def test_reset_primary_flag_clears_all(db_session: AsyncSession):
    listing = await _listing(db_session)
    primary = ListingImage(
        listing_id=listing.id, url="/a.jpg", thumbnail_url="/a_t.jpg", is_primary=True
    )
    secondary = ListingImage(
        listing_id=listing.id, url="/b.jpg", thumbnail_url="/b_t.jpg", is_primary=False
    )
    db_session.add(primary)
    db_session.add(secondary)
    await db_session.flush()

    await reset_primary_flag(db_session, ListingImage, "listing_id", listing.id)
    await db_session.refresh(primary)
    await db_session.refresh(secondary)
    assert primary.is_primary is False
    assert secondary.is_primary is False


async def test_reset_primary_flag_only_affects_owner(db_session: AsyncSession):
    listing_a = await _listing(db_session)
    listing_b = await _listing(db_session)
    img_a = ListingImage(
        listing_id=listing_a.id, url="/a.jpg", thumbnail_url="/a_t.jpg", is_primary=True
    )
    img_b = ListingImage(
        listing_id=listing_b.id, url="/b.jpg", thumbnail_url="/b_t.jpg", is_primary=True
    )
    db_session.add(img_a)
    db_session.add(img_b)
    await db_session.flush()

    await reset_primary_flag(db_session, ListingImage, "listing_id", listing_a.id)
    await db_session.refresh(img_a)
    await db_session.refresh(img_b)
    assert img_a.is_primary is False
    assert img_b.is_primary is True
