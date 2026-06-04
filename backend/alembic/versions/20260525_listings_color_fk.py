"""listings.color -> color_id FK on catalog.colors

Revision ID: c4d7f3a2b815
Revises: b3c5e7a1f209
Create Date: 2026-05-25 16:58:35.471358
"""

from typing import Sequence, Union

from alembic import op

revision: str = "c4d7f3a2b815"
down_revision: Union[str, Sequence[str], None] = "b3c5e7a1f209"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO catalog.colors (id, name_ru, sort_order) "
        "VALUES ('other', 'Другой', 999) "
        "ON CONFLICT (id) DO NOTHING"
    )
    op.execute(
        "ALTER TABLE listings ADD COLUMN IF NOT EXISTS color_id VARCHAR(30)"
    )
    op.execute(
        """
        UPDATE listings l
        SET color_id = COALESCE(
            (
                SELECT c.id FROM catalog.colors c
                WHERE lower(trim(c.name_ru)) = lower(trim(l.color))
                   OR lower(trim(c.name_en)) = lower(trim(l.color))
                   OR lower(c.id) = lower(trim(l.color))
                LIMIT 1
            ),
            'other'
        )
        WHERE color_id IS NULL AND color IS NOT NULL
        """
    )
    op.execute(
        "UPDATE listings SET color_id = 'other' WHERE color_id IS NULL"
    )
    op.execute(
        "ALTER TABLE listings ALTER COLUMN color_id SET NOT NULL"
    )
    op.execute(
        "ALTER TABLE listings "
        "ADD CONSTRAINT fk_listings_color_id "
        "FOREIGN KEY (color_id) REFERENCES catalog.colors (id)"
    )
    op.execute("ALTER TABLE listings DROP COLUMN IF EXISTS color")


def downgrade() -> None:
    op.execute(
        "ALTER TABLE listings ADD COLUMN IF NOT EXISTS color VARCHAR(50)"
    )
    op.execute(
        """
        UPDATE listings l
        SET color = c.name_ru
        FROM catalog.colors c
        WHERE l.color_id = c.id AND l.color IS NULL
        """
    )
    op.execute("ALTER TABLE listings ALTER COLUMN color SET NOT NULL")
    op.execute(
        "ALTER TABLE listings DROP CONSTRAINT IF EXISTS fk_listings_color_id"
    )
    op.execute("ALTER TABLE listings DROP COLUMN IF EXISTS color_id")
