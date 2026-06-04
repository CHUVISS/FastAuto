from typing import Any, cast

import orjson
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.core.cache import cache_get, cache_set
from app.crud import catalog as catalog_crud
from app.models.catalog import CatalogColor
from app.schemas.catalog import (
    ColorDict,
    ConfigurationDict,
    GenerationDict,
    MarkDict,
    ModelDict,
    ModificationDict,
    ModificationFullDict,
)
from app.utils.units import cc_to_litres

_TTL = 3600


def _json_safe(value: Any) -> Any:
    return orjson.loads(orjson.dumps(value, option=orjson.OPT_NON_STR_KEYS))


async def list_colors(session: AsyncSession, redis: Redis) -> list[ColorDict]:
    key = "catalog:colors"
    cached = await cache_get(redis, key)
    if cached is not None:
        return cast(list[ColorDict], cached)
    stmt = select(CatalogColor).order_by(
        col(CatalogColor.sort_order), col(CatalogColor.id)
    )
    rows = (await session.execute(stmt)).scalars().all()
    data: list[ColorDict] = [
        {
            "id": c.id,
            "name_ru": c.name_ru,
            "name_en": c.name_en,
            "hex_code": c.hex_code,
            "sort_order": c.sort_order,
        }
        for c in rows
    ]
    await cache_set(redis, key, data, ttl=_TTL)
    return data


async def _search_marks_db(session: AsyncSession, q: str) -> list[MarkDict]:
    marks = await catalog_crud.search_marks(session, q)
    return [cast(MarkDict, _json_safe(m.to_public_dict())) for m in marks]


async def search_marks(session: AsyncSession, redis: Redis, q: str) -> list[MarkDict]:
    key = f"catalog:marks:{q.lower()}"
    cached = await cache_get(redis, key)
    if cached is not None:
        return cast(list[MarkDict], cached)
    data = await _search_marks_db(session, q)
    await cache_set(redis, key, data, ttl=_TTL)
    return data


async def list_models(
    session: AsyncSession, redis: Redis, mark_id: str
) -> list[ModelDict]:
    key = f"catalog:models:{mark_id}"
    cached = await cache_get(redis, key)
    if cached is not None:
        return cast(list[ModelDict], cached)
    data = [
        cast(ModelDict, _json_safe(m.to_public_dict()))
        for m in await catalog_crud.list_models(session, mark_id)
    ]
    await cache_set(redis, key, data, ttl=_TTL)
    return data


async def list_generations(
    session: AsyncSession, redis: Redis, model_id: str
) -> list[GenerationDict]:
    key = f"catalog:generations:{model_id}"
    cached = await cache_get(redis, key)
    if cached is not None:
        return cast(list[GenerationDict], cached)
    data = [
        cast(GenerationDict, _json_safe(g.to_public_dict()))
        for g in await catalog_crud.list_generations(session, model_id)
    ]
    await cache_set(redis, key, data, ttl=_TTL)
    return data


async def list_configurations(
    session: AsyncSession, redis: Redis, generation_id: str
) -> list[ConfigurationDict]:
    key = f"catalog:configurations:{generation_id}"
    cached = await cache_get(redis, key)
    if cached is not None:
        return cast(list[ConfigurationDict], cached)
    data = [
        cast(ConfigurationDict, _json_safe(c.to_public_dict()))
        for c in await catalog_crud.list_configurations(session, generation_id)
    ]
    await cache_set(redis, key, data, ttl=_TTL)
    return data


async def list_modifications(
    session: AsyncSession, redis: Redis, configuration_id: str
) -> list[ModificationDict]:
    key = f"catalog:modifications:{configuration_id}"
    cached = await cache_get(redis, key)
    if cached is not None:
        return cast(list[ModificationDict], cached)
    data = [
        cast(ModificationDict, _json_safe(m.to_public_dict()))
        for m in await catalog_crud.list_modifications(session, configuration_id)
    ]
    await cache_set(redis, key, data, ttl=_TTL)
    return data


async def _modification_full_db(
    session: AsyncSession, mod_id: str
) -> ModificationFullDict | None:
    full = await catalog_crud.get_modification_full(session, mod_id)
    if full is None:
        return None
    specification = full.specification.to_public_dict() if full.specification else None
    if specification is not None and specification.get("displacement") is not None:
        specification["displacement"] = cc_to_litres(specification["displacement"])
    return cast(
        ModificationFullDict,
        _json_safe(
            {
                "modification": full.modification.to_public_dict(),
                "generation": full.generation.to_public_dict()
                if full.generation
                else None,
                "configuration": full.configuration.to_public_dict()
                if full.configuration
                else None,
                "specification": specification,
                "options": full.options.to_public_dict() if full.options else None,
            }
        ),
    )


async def get_modification_full(
    session: AsyncSession, redis: Redis, mod_id: str
) -> ModificationFullDict | None:
    key = f"catalog:modification_full:{mod_id}"
    cached = await cache_get(redis, key)
    if cached is not None:
        return cast(ModificationFullDict, cached)
    data = await _modification_full_db(session, mod_id)
    if data is None:
        return None
    await cache_set(redis, key, data, ttl=_TTL)
    return data
