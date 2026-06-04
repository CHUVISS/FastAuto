from typing import cast

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, or_, select

from app.core.cache import cache_get, cache_set
from app.models.geo import GeoCity, GeoRegion
from app.schemas.geo import CitiesGrouped, CityDict, RegionDict

_TTL = 3600


def _region_to_dict(r: GeoRegion) -> RegionDict:
    return {
        "id": r.id,
        "code": r.code,
        "iso_code": r.iso_code,
        "name_ru": r.name_ru,
        "fullname_ru": r.fullname_ru,
        "name_en": r.name_en,
        "type_": r.type_,
        "district": r.district,
    }


def _city_to_dict(c: GeoCity) -> CityDict:
    return {
        "id": c.id,
        "region_id": c.region_id,
        "name_ru": c.name_ru,
        "name_en": c.name_en,
        "type_": c.type_,
        "latitude": c.latitude,
        "longitude": c.longitude,
        "timezone": c.timezone,
        "is_capital": c.is_capital,
        "is_popular": c.is_popular,
    }


async def list_regions(session: AsyncSession, redis: Redis) -> list[RegionDict]:
    key = "geo:regions"
    cached = await cache_get(redis, key)
    if cached is not None:
        return cast(list[RegionDict], cached)
    stmt = select(GeoRegion).order_by(col(GeoRegion.name_ru))
    rows = (await session.execute(stmt)).scalars().all()
    data = [_region_to_dict(r) for r in rows]
    await cache_set(redis, key, data, ttl=_TTL)
    return data


async def list_popular_cities(session: AsyncSession, redis: Redis) -> list[CityDict]:
    key = "geo:cities:popular"
    cached = await cache_get(redis, key)
    if cached is not None:
        return cast(list[CityDict], cached)
    stmt = (
        select(GeoCity)
        .where(col(GeoCity.is_popular).is_(True))
        .order_by(col(GeoCity.population).desc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    data = [_city_to_dict(c) for c in rows]
    await cache_set(redis, key, data, ttl=_TTL)
    return data


async def list_cities_grouped(session: AsyncSession, redis: Redis) -> CitiesGrouped:
    key = "geo:cities:grouped"
    cached = await cache_get(redis, key)
    if cached is not None:
        return cast(CitiesGrouped, cached)
    popular_stmt = (
        select(GeoCity)
        .where(col(GeoCity.is_popular).is_(True))
        .order_by(col(GeoCity.population).desc())
    )
    all_stmt = select(GeoCity).order_by(col(GeoCity.name_ru))
    popular = (await session.execute(popular_stmt)).scalars().all()
    all_rows = (await session.execute(all_stmt)).scalars().all()
    data: CitiesGrouped = {
        "popular": [_city_to_dict(c) for c in popular],
        "all": [_city_to_dict(c) for c in all_rows],
    }
    await cache_set(redis, key, data, ttl=_TTL)
    return data


async def search_cities(
    session: AsyncSession,
    redis: Redis,
    q: str,
    region_id: str | None = None,
    limit: int = 30,
) -> list[CityDict]:
    q_norm = q.strip().lower()
    key = f"geo:cities:search:{region_id or 'all'}:{q_norm}"
    cached = await cache_get(redis, key)
    if cached is not None:
        return cast(list[CityDict], cached)
    stmt = select(GeoCity)
    if q_norm:
        like = f"%{q_norm}%"
        stmt = stmt.where(
            or_(
                col(GeoCity.name_ru).ilike(like),
                col(GeoCity.name_en).ilike(like),
            )
        )
    if region_id is not None:
        stmt = stmt.where(col(GeoCity.region_id) == region_id)
    stmt = stmt.order_by(col(GeoCity.name_ru)).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    data = [_city_to_dict(c) for c in rows]
    await cache_set(redis, key, data, ttl=_TTL)
    return data
