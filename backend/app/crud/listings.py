import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from app.models.listings import (
    BookingStatus,
    Listing,
    ListingImage,
    ListingStatus,
    ViewingBooking,
    ViewingWindow,
)

_BASE_SELECT = """
    SELECT l.id, l.year, l.price, l.mileage, l.city_id, l.created_at,
           l.body_type, l.engine_type, l.vin, l.license_plate, l.color_id,
           m.name AS mark_name, mo.name AS model_name,
           gc.name_ru AS city_name,
           s.displacement, s.power
    FROM listings l
    JOIN catalog.marks  m  ON l.mark_id  = m.id
    JOIN catalog.models mo ON l.model_id = mo.id
    JOIN geo.cities     gc ON l.city_id  = gc.id
    LEFT JOIN catalog.specifications s ON l.modification_id = s.id
    WHERE l.status = 'active'
      AND (CAST(:mark_id AS text) IS NULL OR l.mark_id = :mark_id)
      AND (CAST(:model_id AS text) IS NULL OR l.model_id = :model_id)
      AND (CAST(:body_type AS text) IS NULL OR l.body_type = :body_type)
      AND (CAST(:engine_type AS text) IS NULL OR l.engine_type = :engine_type)
      AND (CAST(:city AS text) IS NULL OR l.city_id = :city)
      AND (CAST(:price_min AS bigint) IS NULL OR l.price >= :price_min)
      AND (CAST(:price_max AS bigint) IS NULL OR l.price <= :price_max)
      AND (CAST(:year_min AS int) IS NULL OR l.year >= :year_min)
      AND (CAST(:year_max AS int) IS NULL OR l.year <= :year_max)
"""

_SORTS = {
    "newest": (
        "AND (CAST(:cur_a AS text) IS NULL OR (l.created_at, l.id) < "
        "(CAST(:cur_a AS timestamptz), CAST(:cur_b AS uuid)))",
        "ORDER BY l.created_at DESC, l.id DESC",
    ),
    "price_asc": (
        "AND (CAST(:cur_a AS text) IS NULL OR (l.price, l.id) > "
        "(CAST(:cur_a AS bigint), CAST(:cur_b AS uuid)))",
        "ORDER BY l.price ASC, l.id ASC",
    ),
    "price_desc": (
        "AND (CAST(:cur_a AS text) IS NULL OR (l.price, l.id) < "
        "(CAST(:cur_a AS bigint), CAST(:cur_b AS uuid)))",
        "ORDER BY l.price DESC, l.id DESC",
    ),
}


async def create(session: AsyncSession, listing: Listing) -> Listing:
    session.add(listing)
    return listing


async def get(session: AsyncSession, listing_id: uuid.UUID) -> Listing | None:
    return await session.get(Listing, listing_id)


async def get_for_owner(session: AsyncSession, owner_id: uuid.UUID) -> list[Listing]:
    stmt = (
        select(Listing)
        .where(col(Listing.seller_id) == owner_id)
        .order_by(col(Listing.created_at).desc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def count_active(session: AsyncSession, owner_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(Listing)
        .where(
            col(Listing.seller_id) == owner_id,
            col(Listing.status).in_(
                [
                    ListingStatus.active,
                    ListingStatus.reserved,
                    ListingStatus.pending_review,
                ]
            ),
        )
    )
    return int((await session.execute(stmt)).scalar_one())


async def search_active(
    session: AsyncSession,
    *,
    sort: str = "newest",
    cursor_a: str | None = None,
    cursor_b: str | None = None,
    mark_id: str | None = None,
    model_id: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    body_type: str | None = None,
    engine_type: str | None = None,
    city: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    keyset, order = _SORTS.get(sort, _SORTS["newest"])
    sql = text(f"{_BASE_SELECT}\n      {keyset}\n    {order}\n    LIMIT :limit")
    rows = await session.execute(
        sql,
        {
            "mark_id": mark_id,
            "model_id": model_id,
            "body_type": body_type,
            "engine_type": engine_type,
            "city": city,
            "price_min": price_min,
            "price_max": price_max,
            "year_min": year_min,
            "year_max": year_max,
            "cur_a": cursor_a,
            "cur_b": cursor_b,
            "limit": limit,
        },
    )
    return [dict(r._mapping) | {"id": str(r._mapping["id"])} for r in rows]


async def list_by_status(session: AsyncSession, status: ListingStatus) -> list[Listing]:
    stmt = (
        select(Listing)
        .where(col(Listing.status) == status)
        .order_by(col(Listing.created_at).desc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def count_images(session: AsyncSession, listing_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(ListingImage)
        .where(col(ListingImage.listing_id) == listing_id)
    )
    return int((await session.execute(stmt)).scalar_one())


async def list_images(
    session: AsyncSession, listing_id: uuid.UUID
) -> list[ListingImage]:
    stmt = (
        select(ListingImage)
        .where(col(ListingImage.listing_id) == listing_id)
        .order_by(col(ListingImage.sort_order), col(ListingImage.created_at))
    )
    return list((await session.execute(stmt)).scalars().all())


async def add_image(session: AsyncSession, image: ListingImage) -> ListingImage:
    session.add(image)
    return image


async def get_image(session: AsyncSession, image_id: uuid.UUID) -> ListingImage | None:
    return await session.get(ListingImage, image_id)


async def delete_image(session: AsyncSession, image: ListingImage) -> None:
    await session.delete(image)


async def count_windows(session: AsyncSession, listing_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(ViewingWindow)
        .where(col(ViewingWindow.listing_id) == listing_id)
    )
    return int((await session.execute(stmt)).scalar_one())


async def list_windows(
    session: AsyncSession, listing_id: uuid.UUID
) -> list[ViewingWindow]:
    stmt = (
        select(ViewingWindow)
        .where(col(ViewingWindow.listing_id) == listing_id)
        .order_by(col(ViewingWindow.window_date), col(ViewingWindow.time_from))
    )
    return list((await session.execute(stmt)).scalars().all())


async def add_window(session: AsyncSession, window: ViewingWindow) -> ViewingWindow:
    session.add(window)
    return window


async def get_window(
    session: AsyncSession, window_id: uuid.UUID
) -> ViewingWindow | None:
    return await session.get(ViewingWindow, window_id)


async def delete_window(session: AsyncSession, window: ViewingWindow) -> None:
    await session.delete(window)


async def window_has_active_booking(
    session: AsyncSession, window_id: uuid.UUID
) -> bool:
    stmt = (
        select(func.count())
        .select_from(ViewingBooking)
        .where(
            col(ViewingBooking.window_id) == window_id,
            col(ViewingBooking.status) != BookingStatus.cancelled,
        )
    )
    return int((await session.execute(stmt)).scalar_one()) > 0


async def upsert_windows(
    session: AsyncSession, listing_id: uuid.UUID, windows: list[ViewingWindow]
) -> int:
    if not windows:
        return 0
    rows = [
        {
            "id": uuid.uuid4(),
            "listing_id": listing_id,
            "window_date": w.window_date,
            "time_from": w.time_from,
            "time_to": w.time_to,
        }
        for w in windows
    ]
    stmt = (
        pg_insert(ViewingWindow)
        .values(rows)
        .on_conflict_do_nothing(
            index_elements=["listing_id", "window_date", "time_from", "time_to"]
        )
    )
    await session.execute(stmt)
    return len(rows)
