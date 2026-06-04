import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_users_have_phone_and_role_columns(db_session):
    rows = await db_session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users'"
        )
    )
    cols = {r[0] for r in rows}
    assert {"phone", "phone_verified", "phone_visible", "role"} <= cols


@pytest.mark.asyncio
async def test_users_phone_unique_index_exists(db_session):
    rows = await db_session.execute(
        text("SELECT indexname FROM pg_indexes WHERE tablename='users'")
    )
    names = {r[0] for r in rows}
    assert any("phone" in n for n in names)
