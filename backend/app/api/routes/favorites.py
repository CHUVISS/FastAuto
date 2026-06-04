import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies.auth import CurrentUser, SessionDep
from app.core.config import settings
from app.crud import favorites as favorites_crud
from app.crud import listings as listing_crud
from app.models.listings import Listing
from app.schemas.favorites import FavoriteIn

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=None)
async def list_favorites(user: CurrentUser, session: SessionDep) -> list[Listing]:
    return await favorites_crud.list_for_user(session, user.id)


@router.post("", response_model=None)
async def add_favorite(
    body: FavoriteIn, user: CurrentUser, session: SessionDep
) -> dict[str, Any]:
    if await listing_crud.get(session, body.listing_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Listing not found")
    if await favorites_crud.count_for_user(session, user.id) >= settings.MAX_FAVORITES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Favorites limit reached ({settings.MAX_FAVORITES})",
        )
    added = await favorites_crud.add(session, user.id, body.listing_id)
    await session.commit()
    return {"added": added}


@router.delete("/{listing_id}", response_model=None)
async def remove_favorite(
    listing_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> dict[str, Any]:
    await favorites_crud.remove(session, user.id, listing_id)
    await session.commit()
    return {"removed": True}
