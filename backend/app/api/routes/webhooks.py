from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from app.api.dependencies.auth import RedisDep
from app.core.db import async_session_factory
from app.services.payments import webhook
from app.services.reservations.reservation_service import build_handlers
from app.utils.request import get_client_ip

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/yookassa", response_model=None)
async def yookassa_webhook(request: Request, redis: RedisDep) -> dict[str, Any]:
    if not webhook.is_yookassa_ip(get_client_ip(request)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")
    event = await request.json()
    handlers = build_handlers(async_session_factory, redis)
    processed = await webhook.handle_event(event, redis=redis, handlers=handlers)
    return {"processed": processed}
