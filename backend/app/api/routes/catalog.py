from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.api.dependencies.auth import RedisDep, SessionDep
from app.api.dependencies.rate_limit import public_browse_limit
from app.core.cache import cached_json_response
from app.services.catalog import catalog_service


class _ModificationNotFoundError(Exception):
    pass


router = APIRouter(
    prefix="/catalog",
    tags=["catalog"],
    dependencies=[Depends(public_browse_limit)],
)


@router.get("/colors", response_model=None)
async def list_colors(
    request: Request, session: SessionDep, redis: RedisDep
) -> Response:
    return await cached_json_response(
        request,
        redis,
        key="catalog:colors:raw",
        build=lambda: catalog_service.list_colors(session, redis),
    )


@router.get("/marks", response_model=None)
async def search_marks(
    request: Request,
    session: SessionDep,
    redis: RedisDep,
    q: str = Query(""),
) -> Response:
    return await cached_json_response(
        request,
        redis,
        key=f"catalog:marks:raw:{q.lower()}",
        build=lambda: catalog_service.search_marks(session, redis, q),
    )


@router.get("/marks/{mark_id}/models", response_model=None)
async def list_models(
    request: Request,
    mark_id: str,
    session: SessionDep,
    redis: RedisDep,
) -> Response:
    return await cached_json_response(
        request,
        redis,
        key=f"catalog:models:raw:{mark_id}",
        build=lambda: catalog_service.list_models(session, redis, mark_id),
    )


@router.get("/models/{model_id}/generations", response_model=None)
async def list_generations(
    request: Request,
    model_id: str,
    session: SessionDep,
    redis: RedisDep,
) -> Response:
    return await cached_json_response(
        request,
        redis,
        key=f"catalog:generations:raw:{model_id}",
        build=lambda: catalog_service.list_generations(session, redis, model_id),
    )


@router.get("/generations/{gen_id}/configurations", response_model=None)
async def list_configurations(
    request: Request,
    gen_id: str,
    session: SessionDep,
    redis: RedisDep,
) -> Response:
    return await cached_json_response(
        request,
        redis,
        key=f"catalog:configurations:raw:{gen_id}",
        build=lambda: catalog_service.list_configurations(session, redis, gen_id),
    )


@router.get("/configurations/{conf_id}/modifications", response_model=None)
async def list_modifications(
    request: Request,
    conf_id: str,
    session: SessionDep,
    redis: RedisDep,
) -> Response:
    return await cached_json_response(
        request,
        redis,
        key=f"catalog:modifications:raw:{conf_id}",
        build=lambda: catalog_service.list_modifications(session, redis, conf_id),
    )


@router.get("/modifications/{mod_id}", response_model=None)
async def get_modification(
    request: Request,
    mod_id: str,
    session: SessionDep,
    redis: RedisDep,
) -> Response:
    async def _build() -> dict[str, object]:
        full = await catalog_service.get_modification_full(session, redis, mod_id)
        if full is None:
            raise _ModificationNotFoundError
        return dict(full)

    try:
        return await cached_json_response(
            request,
            redis,
            key=f"catalog:modification_full:raw:{mod_id}",
            build=_build,
        )
    except _ModificationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Modification not found"
        ) from None
