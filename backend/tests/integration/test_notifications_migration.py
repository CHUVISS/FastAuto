import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url

from alembic import command
from app.core.config import settings

pytestmark = pytest.mark.integration


@pytest.fixture
def fresh_pg():
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:17-alpine") as pg:
        yield pg


def test_notifications_table_created_at_head(monkeypatch, fresh_pg):
    u = make_url(fresh_pg.get_connection_url())
    monkeypatch.setattr(settings, "POSTGRES_SERVER", u.host)
    monkeypatch.setattr(settings, "POSTGRES_PORT", u.port)
    monkeypatch.setattr(settings, "POSTGRES_USER", u.username)
    monkeypatch.setattr(settings, "POSTGRES_PASSWORD", u.password)
    monkeypatch.setattr(settings, "POSTGRES_DB", u.database)
    monkeypatch.setattr(settings, "USE_PGBOUNCER", False)

    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")

    eng = create_engine(str(settings.sqlalchemy_sync_database_uri))
    try:
        insp = inspect(eng)
        assert "notifications" in insp.get_table_names()
        cols = {c["name"] for c in insp.get_columns("notifications")}
        assert {"user_id", "type", "payload", "read_at", "created_at"} <= cols
        idx = {i["name"] for i in insp.get_indexes("notifications")}
        assert "idx_notifications_user_unread" in idx
    finally:
        eng.dispose()
