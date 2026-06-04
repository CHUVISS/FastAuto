"""create catalog schema

Revision ID: 82cf852f0775
Revises: cdfc7d8c9c70
Create Date: 2026-05-23 18:51:39.531371

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '82cf852f0775'
down_revision: Union[str, Sequence[str], None] = 'cdfc7d8c9c70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS catalog")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS catalog CASCADE")
