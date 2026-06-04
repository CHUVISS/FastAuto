import logging
import uuid
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import notifications as crud

logger = logging.getLogger(__name__)


async def push(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    notif_type: str,
    payload: dict[str, Any] | None = None,
) -> None:
    try:
        await crud.create(
            session, user_id=user_id, notif_type=notif_type, payload=payload
        )
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        logger.warning(
            "notification push failed",
            extra={"event": "notification_failed", "type": notif_type},
        )
