import pytest
from sqlalchemy import text

from app.crud import catalog as catalog_crud

pytestmark = pytest.mark.integration


async def _seed_catalog(db_session):
    await db_session.execute(
        text(
            "INSERT INTO catalog.marks (id, name, cyrillic_name, popular, country) "
            "VALUES ('BMW', 'BMW', 'БМВ', true, 'Germany'), "
            "       ('AUDI', 'Audi', 'Ауди', false, 'Germany')"
        )
    )
    await db_session.execute(
        text(
            "INSERT INTO catalog.models (id, mark_id, name, cyrillic_name) "
            "VALUES ('BMW_5ER', 'BMW', '5 series', '5 серия')"
        )
    )
    await db_session.execute(
        text(
            "INSERT INTO catalog.generations (id, model_id, name, year_from, year_to) "
            "VALUES ('GEN1', 'BMW_5ER', 'VII (G30) 2016-2023', 2016, 2023)"
        )
    )
    await db_session.execute(
        text(
            "INSERT INTO catalog.configurations (id, generation_id, body_type, doors_count) "
            "VALUES ('CFG1', 'GEN1', 'SEDAN', 4)"
        )
    )
    await db_session.execute(
        text(
            "INSERT INTO catalog.modifications "
            "(id, mark_id, model_id, generation_id, configuration_id, name) "
            "VALUES ('MOD1', 'BMW', 'BMW_5ER', 'GEN1', 'CFG1', '3.0 AT (249 hp) 4WD')"
        )
    )
    await db_session.execute(
        text(
            "INSERT INTO catalog.specifications (id, displacement, power, engine_type) "
            "VALUES ('MOD1', '2993', '249', 'Дизельный')"
        )
    )
    await db_session.execute(
        text(
            "INSERT INTO catalog.options (id, abs, cruise_control) VALUES ('MOD1', true, true)"
        )
    )
    await db_session.flush()


@pytest.mark.asyncio
async def test_search_marks_case_insensitive_popular_first(db_session):
    await _seed_catalog(db_session)
    results = await catalog_crud.search_marks(db_session, "b", limit=10)
    names = [m.name for m in results]
    assert "BMW" in names

    all_results = await catalog_crud.search_marks(db_session, "", limit=10)
    assert all_results[0].popular is True


@pytest.mark.asyncio
async def test_list_models_returns_models_of_mark(db_session):
    await _seed_catalog(db_session)
    models = await catalog_crud.list_models(db_session, "BMW")
    assert [m.id for m in models] == ["BMW_5ER"]


@pytest.mark.asyncio
async def test_list_generations_and_configurations_and_modifications(db_session):
    await _seed_catalog(db_session)
    gens = await catalog_crud.list_generations(db_session, "BMW_5ER")
    assert [g.id for g in gens] == ["GEN1"]
    confs = await catalog_crud.list_configurations(db_session, "GEN1")
    assert [c.id for c in confs] == ["CFG1"]
    mods = await catalog_crud.list_modifications(db_session, "CFG1")
    assert [m.id for m in mods] == ["MOD1"]


@pytest.mark.asyncio
async def test_get_modification_full_joins_all(db_session):
    await _seed_catalog(db_session)
    full = await catalog_crud.get_modification_full(db_session, "MOD1")
    assert full is not None
    assert full.modification.name.startswith("3.0 AT")
    assert full.generation is not None and full.generation.year_to == 2023
    assert full.configuration is not None and full.configuration.body_type == "SEDAN"
    assert full.specification is not None and full.specification.power == "249"
    assert full.options is not None and full.options.abs is True


@pytest.mark.asyncio
async def test_get_modification_full_missing_returns_none(db_session):
    assert await catalog_crud.get_modification_full(db_session, "NOPE") is None
