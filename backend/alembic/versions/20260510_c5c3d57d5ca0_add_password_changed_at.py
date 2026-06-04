"""add_password_changed_at

Revision ID: c5c3d57d5ca0
Revises: a1b2c3d4e5f6
Create Date: 2026-05-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c5c3d57d5ca0"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at "
            "TIMESTAMPTZ NOT NULL DEFAULT NOW()"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("ALTER TABLE users DROP COLUMN IF EXISTS password_changed_at")
    )
