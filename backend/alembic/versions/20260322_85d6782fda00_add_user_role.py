"""add_user_role

Revision ID: 85d6782fda00
Revises: 8db3193d5e83
Create Date: 2026-03-22 00:14:44.104941

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '85d6782fda00'
down_revision: Union[str, Sequence[str], None] = '8db3193d5e83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'user'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
