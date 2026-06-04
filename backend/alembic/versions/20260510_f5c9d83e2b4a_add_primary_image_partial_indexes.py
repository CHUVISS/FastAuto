"""add_primary_image_partial_indexes

Revision ID: f5c9d83e2b4a
Revises: e3a7b52f9d1c
Create Date: 2026-05-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f5c9d83e2b4a"
down_revision: Union[str, None] = "e3a7b52f9d1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_car_images_primary "
            "ON car_images (car_id) WHERE is_primary = true"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_car_offer_images_primary "
            "ON car_offer_images (offer_id) WHERE is_primary = true"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_car_offer_images_primary"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_car_images_primary"))
