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


def _point_settings_at(monkeypatch, pg) -> str:
    u = make_url(pg.get_connection_url())
    monkeypatch.setattr(settings, "POSTGRES_SERVER", u.host)
    monkeypatch.setattr(settings, "POSTGRES_PORT", u.port)
    monkeypatch.setattr(settings, "POSTGRES_USER", u.username)
    monkeypatch.setattr(settings, "POSTGRES_PASSWORD", u.password)
    monkeypatch.setattr(settings, "POSTGRES_DB", u.database)
    monkeypatch.setattr(settings, "USE_PGBOUNCER", False)
    return str(settings.sqlalchemy_sync_database_uri)


def _inspector(sync_url: str):
    eng = create_engine(sync_url, poolclass=None)
    return eng, inspect(eng)


def test_reservation_domain_migration_upgrade_downgrade_upgrade(monkeypatch, fresh_pg):
    """Upgrade to the reservation-domain revision, exercise its downgrade,
    then re-apply head. The destructive cleanup revision (head) is
    forward-only and is verified separately in
    ``test_drop_transactions_payout_migration``.
    """
    sync_url = _point_settings_at(monkeypatch, fresh_pg)
    cfg = Config("alembic.ini")
    reservation_rev = "a1b2c3d4e5f7"
    prior_rev = "b9c1d2e3a407"

    command.upgrade(cfg, reservation_rev)

    eng, insp = _inspector(sync_url)
    try:
        tables = set(insp.get_table_names())
        assert {"reservations", "favorites"} <= tables

        listing_cols = {c["name"] for c in insp.get_columns("listings")}
        assert {"sale_address", "accepts_cash", "accepts_transfer"} <= listing_cols

        booking_cols = {c["name"] for c in insp.get_columns("viewing_bookings")}
        assert "reservation_id" in booking_cols

        res_indexes = {ix["name"] for ix in insp.get_indexes("reservations")}
        assert "uniq_active_reservation_per_listing" in res_indexes

        fav_indexes = {ix["name"] for ix in insp.get_indexes("favorites")}
        assert "uniq_favorite_user_listing" in fav_indexes
    finally:
        eng.dispose()

    # downgrade only the reservation revision, then re-apply
    command.downgrade(cfg, prior_rev)
    eng, insp = _inspector(sync_url)
    try:
        tables = set(insp.get_table_names())
        assert "reservations" not in tables
        assert "favorites" not in tables
        listing_cols = {c["name"] for c in insp.get_columns("listings")}
        assert "sale_address" not in listing_cols
    finally:
        eng.dispose()

    command.upgrade(cfg, reservation_rev)
    eng, insp = _inspector(sync_url)
    try:
        assert {"reservations", "favorites"} <= set(insp.get_table_names())
    finally:
        eng.dispose()
