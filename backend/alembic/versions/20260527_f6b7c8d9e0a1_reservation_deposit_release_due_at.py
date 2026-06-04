"""reservation deposit_release_due_at column for refund delay

Revision ID: f6b7c8d9e0a1
Revises: e5f6a2b3c4d5
Create Date: 2026-05-27
"""

from alembic import op

revision = "f6b7c8d9e0a1"
down_revision = "e5f6a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE reservations "
        "ADD COLUMN IF NOT EXISTS deposit_release_due_at TIMESTAMPTZ"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE reservations DROP COLUMN IF EXISTS deposit_release_due_at"
    )
