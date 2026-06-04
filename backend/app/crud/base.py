from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_pk[T](
    session: AsyncSession, model_class: type[T], pk: Any
) -> T | None:
    return await session.get(model_class, pk)


async def flush_refresh[T](session: AsyncSession, instance: T) -> T:
    await session.flush()
    await session.refresh(instance)
    return instance


async def apply_partial_update[T](
    session: AsyncSession, instance: T, data: dict[str, Any]
) -> T:
    instance.sqlmodel_update(data)  # type: ignore[attr-defined]
    session.add(instance)
    return await flush_refresh(session, instance)


@runtime_checkable
class HasPrimary(Protocol):
    is_primary: bool


async def reset_primary_flag[P: HasPrimary](
    session: AsyncSession,
    model_class: type[P],
    owner_field: str,
    owner_id: Any,
) -> None:
    table = model_class.__table__  # type: ignore[attr-defined]
    await session.execute(
        sa.update(table)
        .where(table.c[owner_field] == owner_id, table.c.is_primary.is_(True))
        .values(is_primary=False)
    )
    await session.flush()
