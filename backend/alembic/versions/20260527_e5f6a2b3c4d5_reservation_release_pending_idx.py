"""reservation release-pending partial index

Revision ID: e5f6a2b3c4d5
Revises: d4e5f8a1b9c2
Create Date: 2026-05-27
"""

from alembic import op

revision = "e5f6a2b3c4d5"
down_revision = "d4e5f8a1b9c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_reservation_release_pending "
        "ON reservations (id) "
        "WHERE status = 'cancelled' AND deposit_released_at IS NULL "
        "AND yk_payment_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_reservation_release_pending")
