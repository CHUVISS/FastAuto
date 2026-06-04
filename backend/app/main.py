from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.api.main import api_router, system_router
from app.api.middleware.access_log import AccessLogMiddleware
from app.api.middleware.request_id import RequestIdMiddleware
from app.core.config import settings
from app.core.db import engine, init_db, sync_engine
from app.core.log import configure_logging, log_startup
from app.core.pre_warm import run_pre_warm
from app.core.redis import close_redis_pool, create_redis_pool, get_redis_client
from app.core.sentry import init_sentry
from app.core.storage import get_image_storage, setup_local_storage
from app.services.scheduler import start_scheduler, stop_scheduler

configure_logging(settings)
init_sentry(settings)

log = structlog.get_logger(__name__)


def _generate_unique_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags else "default"
    return f"{tag}-{route.name}"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    create_redis_pool()
    log.info("redis_pool_ready")

    await get_image_storage().cleanup_tmp()
    await init_db()
    await run_pre_warm(engine, settings.DB_POOL_SIZE, get_redis_client())
    start_scheduler(_app, get_redis_client())
    log_startup(settings)

    yield

    log.info("application_stopping", project=settings.PROJECT_NAME)
    try:
        stop_scheduler(_app)
    finally:
        await close_redis_pool()
        await engine.dispose()
        sync_engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Информационная система «Продажа автомобилей — учёт сделок»",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs"
    if settings.ENVIRONMENT != "production"
    else None,
    redoc_url=f"{settings.API_V1_STR}/redoc"
    if settings.ENVIRONMENT != "production"
    else None,
    generate_unique_id_function=_generate_unique_id,
    lifespan=lifespan,
)

setup_local_storage(app, settings)

app.add_middleware(AccessLogMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(system_router)
