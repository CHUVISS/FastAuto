"""add_sorting_indexes

Revision ID: a3c4e5f6b7d8
Revises: f5c9d83e2b4a
Branch Labels: None
Depends On: None

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3c4e5f6b7d8"
down_revision: Union[str, None] = "f5c9d83e2b4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_cars_price ON cars (price)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_cars_year ON cars (year DESC)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_cars_mileage ON cars (mileage ASC)"
    ))


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_cars_mileage"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_cars_year"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_cars_price"))
