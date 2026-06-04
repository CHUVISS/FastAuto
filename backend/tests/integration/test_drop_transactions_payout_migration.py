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


def _point(monkeypatch, pg) -> str:
    u = make_url(pg.get_connection_url())
    monkeypatch.setattr(settings, "POSTGRES_SERVER", u.host)
    monkeypatch.setattr(settings, "POSTGRES_PORT", u.port)
    monkeypatch.setattr(settings, "POSTGRES_USER", u.username)
    monkeypatch.setattr(settings, "POSTGRES_PASSWORD", u.password)
    monkeypatch.setattr(settings, "POSTGRES_DB", u.database)
    monkeypatch.setattr(settings, "USE_PGBOUNCER", False)
    return str(settings.sqlalchemy_sync_database_uri)


def test_drop_transactions_payout_at_head(monkeypatch, fresh_pg):
    sync_url = _point(monkeypatch, fresh_pg)
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")

    eng = create_engine(sync_url)
    try:
        insp = inspect(eng)
        tables = set(insp.get_table_names())
        assert "transactions" not in tables
        assert "payout_methods" not in tables
        assert "payout_method_audit" not in tables

        listing_cols = {c["name"] for c in insp.get_columns("listings")}
        assert "payout_method_id" not in listing_cols

        # reservation/favorites/tickets-reservation_id intact
        assert "reservations" in tables
        assert "favorites" in tables
        ticket_cols = {c["name"] for c in insp.get_columns("tickets")}
        assert "reservation_id" in ticket_cols
        assert "transaction_id" not in ticket_cols
    finally:
        eng.dispose()
