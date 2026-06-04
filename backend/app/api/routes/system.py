from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["System"])


@router.get("/health", include_in_schema=False)
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.ENVIRONMENT}


if settings.ENVIRONMENT == "local" and settings.SENTRY_DSN:  # pragma: no cover

    @router.get("/sentry-debug", include_in_schema=False)
    async def trigger_error() -> None:
        raise RuntimeError("Sentry verify, this exception is intentional")
