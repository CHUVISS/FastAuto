import pytest
from sqlalchemy import text

from app.crud import listings as listing_crud
from app.models.listings import Condition, Listing, ListingStatus

pytestmark = pytest.mark.integration


async def _seed_catalog_min(db_session):
    for stmt in [
        "INSERT INTO catalog.marks (id, name, popular) VALUES ('BMW','BMW',true) ON CONFLICT DO NOTHING",
        "INSERT INTO catalog.models (id, mark_id, name) VALUES ('BMW_5','BMW','5') ON CONFLICT DO NOTHING",
        "INSERT INTO catalog.generations (id, model_id, name) VALUES ('G1','BMW_5','VII') ON CONFLICT DO NOTHING",
        "INSERT INTO catalog.configurations (id, generation_id, body_type) VALUES ('C1','G1','SEDAN') ON CONFLICT DO NOTHING",
        "INSERT INTO catalog.modifications (id, mark_id, model_id, generation_id, configuration_id, name) "
        "VALUES ('M1','BMW','BMW_5','G1','C1','3.0 AT') ON CONFLICT DO NOTHING",
        "INSERT INTO catalog.specifications (id, engine_type) VALUES ('M1','Дизельный') ON CONFLICT DO NOTHING",
    ]:
        await db_session.execute(text(stmt))


def _draft(seller_id, **over):
    base = {
        "seller_id": seller_id,
        "modification_id": "M1",
        "mark_id": "BMW",
        "model_id": "BMW_5",
        "body_type": "SEDAN",
        "engine_type": "Дизельный",
        "year": 2019,
        "price": 2_500_000,
        "mileage": 85000,
        "color_id": "black",
        "condition": Condition.good,
        "city_id": "7700000000000",
    }
    base.update(over)
    return Listing(**base)


@pytest.mark.asyncio
async def test_create_and_get_for_owner(db_session, regular_user):
    await _seed_catalog_min(db_session)
    created = await listing_crud.create(db_session, _draft(regular_user.id))
    await db_session.flush()
    mine = await listing_crud.get_for_owner(db_session, regular_user.id)
    assert [listing.id for listing in mine] == [created.id]


@pytest.mark.asyncio
async def test_count_active(db_session, regular_user):
    await _seed_catalog_min(db_session)
    db_session.add_all(
        [
            _draft(regular_user.id, status=ListingStatus.active),
            _draft(regular_user.id, status=ListingStatus.draft),
            _draft(regular_user.id, status=ListingStatus.pending_review),
        ]
    )
    await db_session.flush()
    assert await listing_crud.count_active(db_session, regular_user.id) == 2


@pytest.mark.asyncio
async def test_search_active_filters(db_session, regular_user):
    await _seed_catalog_min(db_session)
    active = _draft(regular_user.id, status=ListingStatus.active, price=2_500_000)
    draft = _draft(regular_user.id, status=ListingStatus.draft, price=2_500_000)
    db_session.add_all([active, draft])
    await db_session.flush()

    res = await listing_crud.search_active(
        db_session, mark_id="BMW", price_max=3_000_000
    )
    ids = {r["id"] for r in res}
    assert str(active.id) in ids
    assert str(draft.id) not in ids

    none = await listing_crud.search_active(db_session, price_min=9_000_000)
    assert none == []
