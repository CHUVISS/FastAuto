"""catalog seed state

Revision ID: a8b3c1f2d4e5
Revises: f7a1b8c2d3e4
Create Date: 2026-05-25 04:06:08.363137
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a8b3c1f2d4e5"
down_revision: Union[str, Sequence[str], None] = "f7a1b8c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS catalog")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS catalog._seed_state (
            source_name   VARCHAR(50)  NOT NULL,
            source_sha256 VARCHAR(64)  NOT NULL,
            applied_at    TIMESTAMPTZ  NOT NULL,
            row_count     INTEGER,
            CONSTRAINT pk_catalog_seed_state PRIMARY KEY (source_name)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS catalog._seed_state")
