"""catalog colors

Revision ID: b3c5e7a1f209
Revises: a8b3c1f2d4e5
Create Date: 2026-05-25 03:30:00.341761
"""

from typing import Sequence, Union

from alembic import op

revision: str = "b3c5e7a1f209"
down_revision: Union[str, Sequence[str], None] = "a8b3c1f2d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS catalog")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS catalog.colors (
            id         VARCHAR(30) NOT NULL,
            name_ru    VARCHAR(50) NOT NULL,
            name_en    VARCHAR(50),
            hex_code   VARCHAR(7),
            sort_order INTEGER NOT NULL DEFAULT 0,
            CONSTRAINT pk_catalog_colors PRIMARY KEY (id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_catalog_colors_sort "
        "ON catalog.colors (sort_order, id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS catalog.colors")
