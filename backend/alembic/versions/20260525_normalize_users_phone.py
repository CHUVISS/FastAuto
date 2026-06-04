"""normalize users.phone to canonical 7XXXXXXXXXX

Revision ID: f7a2c5b9e304
Revises: e5f1b6d3a482
Create Date: 2026-05-25 17:38:51.318643
"""

from typing import Sequence, Union

from alembic import op

revision: str = "f7a2c5b9e304"
down_revision: Union[str, Sequence[str], None] = "e5f1b6d3a482"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET phone = NULLIF(
            CASE
                WHEN regexp_replace(phone, '\\D', '', 'g') ~ '^8[0-9]{10}$'
                    THEN '7' || substring(regexp_replace(phone, '\\D', '', 'g') from 2)
                ELSE regexp_replace(phone, '\\D', '', 'g')
            END,
            ''
        )
        WHERE phone IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE users SET phone = NULL
        WHERE phone IS NOT NULL
          AND (length(phone) != 11 OR substring(phone, 1, 1) != '7')
        """
    )


def downgrade() -> None:
    pass
