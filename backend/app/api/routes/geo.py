from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.dependencies.auth import RedisDep, SessionDep
from app.api.dependencies.rate_limit import public_browse_limit
from app.core.cache import cached_json_response
from app.services.geo import geo_service

router = APIRouter(
    prefix="/geo",
    tags=["geo"],
    dependencies=[Depends(public_browse_limit)],
)


@router.get("/regions", response_model=None)
async def list_regions(
    request: Request, session: SessionDep, redis: RedisDep
) -> Response:
    return await cached_json_response(
        request,
        redis,
        key="geo:regions:raw",
        build=lambda: geo_service.list_regions(session, redis),
    )


@router.get("/cities", response_model=None)
async def cities(
    request: Request,
    session: SessionDep,
    redis: RedisDep,
    q: str = Query("", description="Поиск по названию (ILIKE name_ru/name_en)"),
    region_id: str | None = Query(None, description="ФИАС-id региона"),
    all: bool = Query(  # noqa: A002
        False,
        description=(
            "Если true — отдаёт полный список (~1102 города, ~250 KB JSON). "
            "По умолчанию возвращает только популярные города (~15)."
        ),
    ),
) -> Response:
    q_norm = q.strip().lower()
    if q_norm or region_id is not None:
        return await cached_json_response(
            request,
            redis,
            key=f"geo:cities:search:raw:{region_id or 'all'}:{q_norm}",
            build=lambda: geo_service.search_cities(session, redis, q, region_id),
        )
    if all:
        return await cached_json_response(
            request,
            redis,
            key="geo:cities:grouped:raw",
            build=lambda: geo_service.list_cities_grouped(session, redis),
        )
    return await cached_json_response(
        request,
        redis,
        key="geo:cities:popular:raw",
        build=lambda: geo_service.list_popular_cities(session, redis),
    )
