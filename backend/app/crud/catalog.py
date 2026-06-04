from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.models.catalog import (
    Configuration,
    Generation,
    Mark,
    Model,
    Modification,
    Options,
    Specification,
)


@dataclass
class ModificationFull:
    modification: Modification
    generation: Generation | None
    configuration: Configuration | None
    specification: Specification | None
    options: Options | None


async def search_marks(session: AsyncSession, q: str, limit: int = 30) -> list[Mark]:
    stmt = select(Mark)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            col(Mark.name).ilike(like) | col(Mark.cyrillic_name).ilike(like)
        )
    stmt = stmt.order_by(col(Mark.popular).desc(), col(Mark.name)).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def list_models(session: AsyncSession, mark_id: str) -> list[Model]:
    stmt = select(Model).where(col(Model.mark_id) == mark_id).order_by(col(Model.name))
    return list((await session.execute(stmt)).scalars().all())


async def list_generations(session: AsyncSession, model_id: str) -> list[Generation]:
    stmt = (
        select(Generation)
        .where(col(Generation.model_id) == model_id)
        .order_by(col(Generation.name))
    )
    return list((await session.execute(stmt)).scalars().all())


async def list_configurations(
    session: AsyncSession, generation_id: str
) -> list[Configuration]:
    stmt = select(Configuration).where(
        col(Configuration.generation_id) == generation_id
    )
    return list((await session.execute(stmt)).scalars().all())


async def list_modifications(
    session: AsyncSession, configuration_id: str
) -> list[Modification]:
    stmt = (
        select(Modification)
        .where(col(Modification.configuration_id) == configuration_id)
        .order_by(col(Modification.name))
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_modification_full(
    session: AsyncSession, mod_id: str
) -> ModificationFull | None:
    mod = await session.get(Modification, mod_id)
    if mod is None:
        return None
    gen = (
        await session.get(Generation, mod.generation_id) if mod.generation_id else None
    )
    conf = (
        await session.get(Configuration, mod.configuration_id)
        if mod.configuration_id
        else None
    )
    spec = await session.get(Specification, mod_id)
    opts = await session.get(Options, mod_id)
    return ModificationFull(
        modification=mod,
        generation=gen,
        configuration=conf,
        specification=spec,
        options=opts,
    )
