import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_catalog_schema_and_marks_table_exist(db_session):
    schema = await db_session.execute(
        text(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name='catalog'"
        )
    )
    assert schema.first() is not None
    tbl = await db_session.execute(text("SELECT to_regclass('catalog.marks')"))
    assert tbl.scalar() is not None
