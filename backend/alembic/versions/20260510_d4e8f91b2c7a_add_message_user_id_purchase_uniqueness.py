"""add_message_user_id_purchase_uniqueness

Revision ID: d4e8f91b2c7a
Revises: b7e9f21a3d8c
Create Date: 2026-05-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e8f91b2c7a"
down_revision: Union[str, None] = "b7e9f21a3d8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS user_id UUID")
    )
    op.execute(
        sa.text(
            "DO $$ BEGIN "
            "IF NOT EXISTS ("
            "  SELECT 1 FROM pg_constraint "
            "  WHERE conname = 'fk_messages_user_id' AND conrelid = 'messages'::regclass"
            ") THEN "
            "  ALTER TABLE messages ADD CONSTRAINT fk_messages_user_id "
            "  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL; "
            "END IF; END $$"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_messages_user_id ON messages (user_id)"
        )
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uniq_active_purchase_inquiry "
            "ON messages(user_id, car_id) "
            "WHERE message_type = 'inquiry' AND status IN ('new', 'in_progress') "
            "AND user_id IS NOT NULL AND car_id IS NOT NULL"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS uniq_active_purchase_inquiry"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_messages_user_id"))
    op.execute(
        sa.text(
            "ALTER TABLE messages DROP CONSTRAINT IF EXISTS fk_messages_user_id"
        )
    )
    op.execute(
        sa.text("ALTER TABLE messages DROP COLUMN IF EXISTS user_id")
    )
