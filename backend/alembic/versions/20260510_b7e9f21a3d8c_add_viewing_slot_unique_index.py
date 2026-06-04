"""add_viewing_slot_unique_index

Revision ID: b7e9f21a3d8c
Revises: c5c3d57d5ca0
Create Date: 2026-05-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7e9f21a3d8c"
down_revision: Union[str, None] = "c5c3d57d5ca0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uniq_viewing_active_slot "
            "ON viewings(car_id, viewing_date, viewing_time) "
            "WHERE result IN ('scheduled', 'confirmed') AND viewing_time IS NOT NULL"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS uniq_viewing_active_slot"))
