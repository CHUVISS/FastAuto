import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from app.models.favorites import Favorite
from app.models.listings import Listing


async def add(session: AsyncSession, user_id: uuid.UUID, listing_id: uuid.UUID) -> bool:
    stmt = (
        pg_insert(Favorite)
        .values(id=uuid.uuid4(), user_id=user_id, listing_id=listing_id)
        .on_conflict_do_nothing(index_elements=["user_id", "listing_id"])
        .returning(col(Favorite.id))
    )
    inserted = (await session.execute(stmt)).first()
    return inserted is not None


async def remove(
    session: AsyncSession, user_id: uuid.UUID, listing_id: uuid.UUID
) -> None:
    stmt = select(Favorite).where(
        col(Favorite.user_id) == user_id,
        col(Favorite.listing_id) == listing_id,
    )
    favorite = (await session.execute(stmt)).scalars().first()
    if favorite is not None:
        await session.delete(favorite)


async def list_for_user(session: AsyncSession, user_id: uuid.UUID) -> list[Listing]:
    stmt = (
        select(Listing)
        .join(Favorite, col(Favorite.listing_id) == col(Listing.id))
        .where(col(Favorite.user_id) == user_id)
        .order_by(col(Favorite.created_at).desc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def count_for_user(session: AsyncSession, user_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(Favorite)
        .where(col(Favorite.user_id) == user_id)
    )
    return int((await session.execute(stmt)).scalar_one())


async def count_for_listing(session: AsyncSession, listing_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(Favorite)
        .where(col(Favorite.listing_id) == listing_id)
    )
    return int((await session.execute(stmt)).scalar_one())
