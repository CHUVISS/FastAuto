"""add_composite_status_sort_indexes

Revision ID: b2d4f6a8c1e3
Revises: a3c4e5f6b7d8
Branch Labels: None
Depends On: None

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2d4f6a8c1e3"
down_revision: Union[str, None] = "a3c4e5f6b7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite (status, sort_col) indexes: planner can satisfy both
    # WHERE status IN (...) and ORDER BY sort_col in a single index scan.
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_cars_status_price "
        "ON cars (status, price ASC)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_cars_status_year "
        "ON cars (status, year DESC)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_cars_status_mileage "
        "ON cars (status, mileage ASC)"
    ))
    # Covering index for the count query: COUNT(*) WHERE status IN (...)
    # uses this without touching the heap when status is the only predicate.
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_cars_status "
        "ON cars (status)"
    ))


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_cars_status"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_cars_status_mileage"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_cars_status_year"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_cars_status_price"))
