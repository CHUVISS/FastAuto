import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies.auth import CurrentUser, SessionDep
from app.crud import notifications as crud
from app.models.notifications import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=None)
async def list_notifications(
    user: CurrentUser, session: SessionDep, unread: bool = False
) -> list[Notification]:
    return await crud.list_for_user(session, user.id, unread_only=unread)


@router.post("/{notification_id}/read", response_model=None)
async def mark_read(
    notification_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> dict[str, Any]:
    notification = await crud.get(session, notification_id)
    if notification is None or notification.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if notification.read_at is None:
        notification.read_at = datetime.now(UTC)
        await session.commit()
    return {"read": True}


@router.post("/read-all", response_model=None)
async def mark_all_read(user: CurrentUser, session: SessionDep) -> dict[str, Any]:
    updated = await crud.mark_all_read(session, user.id)
    await session.commit()
    return {"marked_read": updated}
