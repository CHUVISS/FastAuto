"""listings.city_of_sale -> city_id FK on geo.cities

Revision ID: e5f1b6d3a482
Revises: d6e9b4c8a371
Create Date: 2026-05-25 15:41:37.218643
"""

from typing import Sequence, Union

from alembic import op

revision: str = "e5f1b6d3a482"
down_revision: Union[str, Sequence[str], None] = "d6e9b4c8a371"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE listings ADD COLUMN IF NOT EXISTS city_id VARCHAR(13)"
    )
    op.execute(
        """
        UPDATE listings l
        SET city_id = (
            SELECT c.id FROM geo.cities c
            WHERE lower(trim(c.name_ru)) = lower(trim(l.city_of_sale))
               OR lower(trim(c.name_en)) = lower(trim(l.city_of_sale))
            ORDER BY c.population DESC NULLS LAST
            LIMIT 1
        )
        WHERE city_id IS NULL AND city_of_sale IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE listings
        SET city_id = (
            SELECT c.id FROM geo.cities c
            WHERE c.is_capital = true
            ORDER BY c.population DESC NULLS LAST
            LIMIT 1
        )
        WHERE city_id IS NULL
          AND EXISTS (SELECT 1 FROM geo.cities)
        """
    )
    op.execute("ALTER TABLE listings ALTER COLUMN city_id SET NOT NULL")
    op.execute(
        "ALTER TABLE listings "
        "ADD CONSTRAINT fk_listings_city_id "
        "FOREIGN KEY (city_id) REFERENCES geo.cities (id)"
    )
    op.execute("ALTER TABLE listings DROP COLUMN IF EXISTS city_of_sale")


def downgrade() -> None:
    op.execute(
        "ALTER TABLE listings ADD COLUMN IF NOT EXISTS city_of_sale VARCHAR(100)"
    )
    op.execute(
        """
        UPDATE listings l
        SET city_of_sale = c.name_ru
        FROM geo.cities c
        WHERE l.city_id = c.id AND l.city_of_sale IS NULL
        """
    )
    op.execute(
        "UPDATE listings SET city_of_sale = '' WHERE city_of_sale IS NULL"
    )
    op.execute("ALTER TABLE listings ALTER COLUMN city_of_sale SET NOT NULL")
    op.execute(
        "ALTER TABLE listings DROP CONSTRAINT IF EXISTS fk_listings_city_id"
    )
    op.execute("ALTER TABLE listings DROP COLUMN IF EXISTS city_id")
