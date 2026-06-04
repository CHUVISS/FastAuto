from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration


def _write_source(tmp_path: Path, content: bytes) -> Path:
    p = tmp_path / "src.sql"
    p.write_bytes(content)
    return p


@pytest.mark.asyncio
async def test_first_seed_invokes_loader_and_records_state(
    monkeypatch, tmp_path, pg_container
):
    from sqlalchemy import create_engine

    from scripts import seed_catalog as sc

    source_name = f"cars_{uuid.uuid4().hex[:6]}"
    src = _write_source(tmp_path, b"-- dump v1\nINSERT INTO marks VALUES (1);")
    expected_hash = hashlib.sha256(src.read_bytes()).hexdigest()

    loader = MagicMock(return_value=42)
    monkeypatch.setitem(
        sc._SOURCES,
        source_name,
        sc.Source(name=source_name, path=src, loader=loader),
    )
    sync_url = pg_container.get_connection_url().replace("psycopg2", "psycopg")
    sync_eng = create_engine(sync_url)
    monkeypatch.setattr("app.core.db.sync_engine", sync_eng)

    with sync_eng.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS catalog"))
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS catalog._seed_state ("
                " source_name VARCHAR(50) PRIMARY KEY,"
                " source_sha256 VARCHAR(64) NOT NULL,"
                " applied_at TIMESTAMPTZ NOT NULL,"
                " row_count INTEGER)"
            )
        )

    code = sc.run(source=source_name, force=False)
    assert code == 0
    loader.assert_called_once_with(src)

    with sync_eng.connect() as conn:
        row = conn.execute(
            text(
                "SELECT source_sha256, row_count FROM catalog._seed_state "
                "WHERE source_name = :n"
            ),
            {"n": source_name},
        ).first()
    assert row is not None
    assert row[0] == expected_hash
    assert row[1] == 42

    sync_eng.dispose()


@pytest.mark.asyncio
async def test_unchanged_hash_skips_loader(monkeypatch, tmp_path, pg_container):
    from sqlalchemy import create_engine

    from scripts import seed_catalog as sc

    source_name = f"cars_{uuid.uuid4().hex[:6]}"
    src = _write_source(tmp_path, b"-- dump v1")

    loader = MagicMock(return_value=1)
    monkeypatch.setitem(
        sc._SOURCES,
        source_name,
        sc.Source(name=source_name, path=src, loader=loader),
    )
    sync_url = pg_container.get_connection_url().replace("psycopg2", "psycopg")
    sync_eng = create_engine(sync_url)
    monkeypatch.setattr("app.core.db.sync_engine", sync_eng)

    with sync_eng.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS catalog"))
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS catalog._seed_state ("
                " source_name VARCHAR(50) PRIMARY KEY,"
                " source_sha256 VARCHAR(64) NOT NULL,"
                " applied_at TIMESTAMPTZ NOT NULL,"
                " row_count INTEGER)"
            )
        )

    sc.run(source=source_name, force=False)
    assert loader.call_count == 1

    sc.run(source=source_name, force=False)
    assert loader.call_count == 1

    sync_eng.dispose()


@pytest.mark.asyncio
async def test_changed_hash_triggers_reseed(monkeypatch, tmp_path, pg_container):
    from sqlalchemy import create_engine

    from scripts import seed_catalog as sc

    source_name = f"cars_{uuid.uuid4().hex[:6]}"
    src = _write_source(tmp_path, b"-- dump v1")

    loader = MagicMock(return_value=1)
    monkeypatch.setitem(
        sc._SOURCES,
        source_name,
        sc.Source(name=source_name, path=src, loader=loader),
    )
    sync_url = pg_container.get_connection_url().replace("psycopg2", "psycopg")
    sync_eng = create_engine(sync_url)
    monkeypatch.setattr("app.core.db.sync_engine", sync_eng)

    with sync_eng.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS catalog"))
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS catalog._seed_state ("
                " source_name VARCHAR(50) PRIMARY KEY,"
                " source_sha256 VARCHAR(64) NOT NULL,"
                " applied_at TIMESTAMPTZ NOT NULL,"
                " row_count INTEGER)"
            )
        )

    sc.run(source=source_name, force=False)
    src.write_bytes(b"-- dump v2 (changed)")

    sc.run(source=source_name, force=False)
    assert loader.call_count == 2

    sync_eng.dispose()


@pytest.mark.asyncio
async def test_force_reseeds_even_if_hash_matches(monkeypatch, tmp_path, pg_container):
    from sqlalchemy import create_engine

    from scripts import seed_catalog as sc

    source_name = f"cars_{uuid.uuid4().hex[:6]}"
    src = _write_source(tmp_path, b"-- dump v1")

    loader = MagicMock(return_value=1)
    monkeypatch.setitem(
        sc._SOURCES,
        source_name,
        sc.Source(name=source_name, path=src, loader=loader),
    )
    sync_url = pg_container.get_connection_url().replace("psycopg2", "psycopg")
    sync_eng = create_engine(sync_url)
    monkeypatch.setattr("app.core.db.sync_engine", sync_eng)

    with sync_eng.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS catalog"))
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS catalog._seed_state ("
                " source_name VARCHAR(50) PRIMARY KEY,"
                " source_sha256 VARCHAR(64) NOT NULL,"
                " applied_at TIMESTAMPTZ NOT NULL,"
                " row_count INTEGER)"
            )
        )

    sc.run(source=source_name, force=False)
    sc.run(source=source_name, force=True)
    assert loader.call_count == 2

    sync_eng.dispose()
