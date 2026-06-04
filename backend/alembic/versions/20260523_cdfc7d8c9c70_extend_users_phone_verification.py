"""extend users phone verification

Revision ID: cdfc7d8c9c70
Revises: b2d4f6a8c1e3
Create Date: 2026-05-23 11:54:20.047895

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'cdfc7d8c9c70'
down_revision: Union[str, Sequence[str], None] = 'b2d4f6a8c1e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
        "phone_verified BOOLEAN NOT NULL DEFAULT FALSE"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
        "phone_visible BOOLEAN NOT NULL DEFAULT TRUE"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_phone "
        "ON users(phone) WHERE phone IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_users_phone")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS phone_visible")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS phone_verified")
