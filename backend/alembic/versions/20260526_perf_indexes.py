"""perf indexes: tickets created_at

Revision ID: a1b2c3d4e5f6
Revises: f7a2c5b9e304
Create Date: 2026-05-26 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "b9c1d2e3a407"
down_revision: Union[str, Sequence[str], None] = "f7a2c5b9e304"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tickets_created_desc "
        "ON tickets (created_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_tickets_created_desc")
