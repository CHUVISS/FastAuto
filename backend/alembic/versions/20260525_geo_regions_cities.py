"""geo schema + regions + cities

Revision ID: d6e9b4c8a371
Revises: c4d7f3a2b815
Create Date: 2026-05-25 05:48:12.188513
"""

from typing import Sequence, Union

from alembic import op

revision: str = "d6e9b4c8a371"
down_revision: Union[str, Sequence[str], None] = "c4d7f3a2b815"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS geo")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS geo.regions (
            id           VARCHAR(13) NOT NULL,
            code         VARCHAR(10) NOT NULL,
            iso_code     VARCHAR(10) NOT NULL,
            name_ru      VARCHAR(100) NOT NULL,
            fullname_ru  VARCHAR(200) NOT NULL,
            name_en      VARCHAR(100),
            type_        VARCHAR(50) NOT NULL,
            district     VARCHAR(50),
            okato        VARCHAR(20),
            population   INTEGER,
            CONSTRAINT pk_geo_regions PRIMARY KEY (id),
            CONSTRAINT uq_geo_regions_code UNIQUE (code),
            CONSTRAINT uq_geo_regions_iso UNIQUE (iso_code)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS geo.cities (
            id          VARCHAR(13) NOT NULL,
            region_id   VARCHAR(13) NOT NULL,
            name_ru     VARCHAR(100) NOT NULL,
            name_en     VARCHAR(100),
            type_       VARCHAR(50) NOT NULL,
            latitude    DOUBLE PRECISION,
            longitude   DOUBLE PRECISION,
            timezone    VARCHAR(50),
            population  INTEGER,
            is_capital  BOOLEAN NOT NULL DEFAULT false,
            is_popular  BOOLEAN NOT NULL DEFAULT false,
            okato       VARCHAR(20),
            zip_code    VARCHAR(10),
            CONSTRAINT pk_geo_cities PRIMARY KEY (id),
            CONSTRAINT fk_geo_cities_region
                FOREIGN KEY (region_id) REFERENCES geo.regions (id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_cities_region ON geo.cities (region_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_cities_name_trgm "
        "ON geo.cities USING gin (name_ru gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_cities_popular ON geo.cities (is_popular)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS geo.cities")
    op.execute("DROP TABLE IF EXISTS geo.regions")
    op.execute("DROP SCHEMA IF EXISTS geo")
