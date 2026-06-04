"""add_pg_trgm_indexes

Revision ID: e3a7b52f9d1c
Revises: d4e8f91b2c7a
Create Date: 2026-05-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e3a7b52f9d1c"
down_revision: Union[str, None] = "d4e8f91b2c7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_cars_brand_trgm "
            "ON cars USING GIN (lower(brand) gin_trgm_ops)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_cars_model_trgm "
            "ON cars USING GIN (lower(model) gin_trgm_ops)"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_cars_model_trgm"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_cars_brand_trgm"))
