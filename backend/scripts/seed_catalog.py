from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import structlog
from sqlalchemy import text

from app.core.config import settings
from app.core.log import configure_logging
from scripts.import_catalog import load_cars_catalog

configure_logging(settings)
log = structlog.get_logger("seed_catalog")

_REPO_BACKEND = Path(__file__).resolve().parent.parent
_DATA_DIR = _REPO_BACKEND / "data"
_CARS_DUMP = _DATA_DIR / "carsbase2_dump.sql"
_COLORS_JSON = _DATA_DIR / "catalog_colors.json"
_REGIONS_JSON = _DATA_DIR / "russia-regions.json"
_CITIES_JSON = _DATA_DIR / "russia-cities.json"


@dataclass(frozen=True)
class Source:
    name: str
    path: Path
    loader: Callable[[Path], int]


def load_colors(path: Path) -> int:
    from app.core.db import sync_engine

    rows = json.loads(path.read_text(encoding="utf-8"))
    with sync_engine.begin() as conn:
        for row in rows:
            conn.execute(
                text(
                    """
                    INSERT INTO catalog.colors (id, name_ru, name_en, hex_code, sort_order)
                    VALUES (:id, :name_ru, :name_en, :hex_code, :sort_order)
                    ON CONFLICT (id) DO UPDATE
                    SET name_ru    = EXCLUDED.name_ru,
                        name_en    = EXCLUDED.name_en,
                        hex_code   = EXCLUDED.hex_code,
                        sort_order = EXCLUDED.sort_order
                    """
                ),
                row,
            )
    return len(rows)


def load_regions(path: Path) -> int:
    from app.core.db import sync_engine

    items = json.loads(path.read_text(encoding="utf-8"))
    rows = [
        {
            "id": r["id"],
            "code": r["code"],
            "iso_code": r["iso_3166-2"],
            "name_ru": r["name"],
            "fullname_ru": r.get("fullname") or r["name"],
            "name_en": r.get("name_en"),
            "type_": r.get("type") or "",
            "district": r.get("district"),
            "okato": r.get("okato"),
            "population": r.get("population"),
        }
        for r in items
    ]
    with sync_engine.begin() as conn:
        for row in rows:
            conn.execute(
                text(
                    """
                    INSERT INTO geo.regions
                        (id, code, iso_code, name_ru, fullname_ru, name_en,
                         type_, district, okato, population)
                    VALUES
                        (:id, :code, :iso_code, :name_ru, :fullname_ru, :name_en,
                         :type_, :district, :okato, :population)
                    ON CONFLICT (id) DO UPDATE
                    SET code        = EXCLUDED.code,
                        iso_code    = EXCLUDED.iso_code,
                        name_ru     = EXCLUDED.name_ru,
                        fullname_ru = EXCLUDED.fullname_ru,
                        name_en     = EXCLUDED.name_en,
                        type_       = EXCLUDED.type_,
                        district    = EXCLUDED.district,
                        okato       = EXCLUDED.okato,
                        population  = EXCLUDED.population
                    """
                ),
                row,
            )
    return len(rows)


def load_cities(path: Path) -> int:
    from app.core.config import settings
    from app.core.db import sync_engine

    items = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for c in items:
        region = c.get("region") or {}
        coords = c.get("coords") or {}
        tz = c.get("timezone") or {}
        rows.append(
            {
                "id": c["id"],
                "region_id": region.get("id"),
                "name_ru": c["name"],
                "name_en": c.get("name_en"),
                "type_": c.get("type") or "",
                "latitude": coords.get("lat"),
                "longitude": coords.get("lon"),
                "timezone": tz.get("tzid"),
                "population": c.get("population"),
                "is_capital": bool(c.get("isCapital", False)),
                "okato": c.get("okato"),
                "zip_code": str(c["zip"]) if c.get("zip") is not None else None,
            }
        )
    with sync_engine.begin() as conn:
        for row in rows:
            conn.execute(
                text(
                    """
                    INSERT INTO geo.cities
                        (id, region_id, name_ru, name_en, type_, latitude, longitude,
                         timezone, population, is_capital, is_popular, okato, zip_code)
                    VALUES
                        (:id, :region_id, :name_ru, :name_en, :type_, :latitude, :longitude,
                         :timezone, :population, :is_capital, false, :okato, :zip_code)
                    ON CONFLICT (id) DO UPDATE
                    SET region_id  = EXCLUDED.region_id,
                        name_ru    = EXCLUDED.name_ru,
                        name_en    = EXCLUDED.name_en,
                        type_      = EXCLUDED.type_,
                        latitude   = EXCLUDED.latitude,
                        longitude  = EXCLUDED.longitude,
                        timezone   = EXCLUDED.timezone,
                        population = EXCLUDED.population,
                        is_capital = EXCLUDED.is_capital,
                        okato      = EXCLUDED.okato,
                        zip_code   = EXCLUDED.zip_code
                    """
                ),
                row,
            )
        conn.execute(text("UPDATE geo.cities SET is_popular = false"))
        conn.execute(
            text(
                """
                UPDATE geo.cities SET is_popular = true
                WHERE id IN (
                    SELECT id FROM geo.cities
                    WHERE population IS NOT NULL
                    ORDER BY population DESC
                    LIMIT :lim
                )
                """
            ),
            {"lim": settings.CITIES_POPULAR_LIMIT},
        )
    return len(rows)


_SOURCES: dict[str, Source] = {
    "cars": Source(name="cars", path=_CARS_DUMP, loader=load_cars_catalog),
    "colors": Source(name="colors", path=_COLORS_JSON, loader=load_colors),
    "regions": Source(name="regions", path=_REGIONS_JSON, loader=load_regions),
    "cities": Source(name="cities", path=_CITIES_JSON, loader=load_cities),
}


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_state(conn, source_name: str) -> str | None:
    row = conn.execute(
        text("SELECT source_sha256 FROM catalog._seed_state WHERE source_name = :n"),
        {"n": source_name},
    ).first()
    return row[0] if row else None


def _write_state(conn, source_name: str, sha256: str, row_count: int | None) -> None:
    conn.execute(
        text(
            """
            INSERT INTO catalog._seed_state (source_name, source_sha256, applied_at, row_count)
            VALUES (:n, :h, :a, :c)
            ON CONFLICT (source_name) DO UPDATE
            SET source_sha256 = EXCLUDED.source_sha256,
                applied_at    = EXCLUDED.applied_at,
                row_count     = EXCLUDED.row_count
            """
        ),
        {
            "n": source_name,
            "h": sha256,
            "a": datetime.now(UTC),
            "c": row_count,
        },
    )


def _run_one(source: Source, *, force: bool) -> bool:
    from app.core.db import sync_engine

    if not source.path.exists():
        log.warning(
            "source_not_found",
            source=source.name,
            path=str(source.path),
        )
        return True

    file_hash = _sha256_of_file(source.path)
    with sync_engine.begin() as conn:
        applied = _read_state(conn, source.name)

    if applied == file_hash and not force:
        log.info("up_to_date", source=source.name, sha256=file_hash[:12])
        return True

    if applied is None:
        log.info("first_seed", source=source.name, sha256=file_hash[:12])
    elif force:
        log.info("forced_reseed", source=source.name, sha256=file_hash[:12])
    else:
        log.info(
            "source_changed",
            source=source.name,
            old_sha256=applied[:12],
            new_sha256=file_hash[:12],
        )

    row_count = source.loader(source.path)

    with sync_engine.begin() as conn:
        _write_state(conn, source.name, file_hash, row_count)
    log.info("seeded", source=source.name, row_count=row_count)
    return True


def run(source: str = "all", *, force: bool = False) -> int:
    if source == "all":
        chosen = list(_SOURCES.values())
    else:
        if source not in _SOURCES:
            log.error("unknown_source", source=source, known=list(_SOURCES))
            return 2
        chosen = [_SOURCES[source]]

    failures = 0
    for src in chosen:
        if not _run_one(src, force=force):
            failures += 1
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="seed_catalog")
    parser.add_argument(
        "--source",
        default="all",
        choices=["all", *_SOURCES.keys()],
        help="which catalog source to seed (default: all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="reseed even if the source hash matches the last applied state",
    )
    args = parser.parse_args(argv)
    return run(source=args.source, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
