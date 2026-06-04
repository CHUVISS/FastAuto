from typing import Annotated

from fastapi import Depends, Query
from pydantic import BaseModel

from app.core.config import settings


class PaginationParams(BaseModel):
    skip: int = Query(default=0, ge=0, description="Смещение от начала списка")
    limit: int = Query(
        default=settings.PAGINATION_DEFAULT_LIMIT,
        ge=1,
        le=settings.PAGINATION_MAX_LIMIT,
        description=f"Количество записей (макс. {settings.PAGINATION_MAX_LIMIT})",
    )


PaginationDep = Annotated[PaginationParams, Depends()]
