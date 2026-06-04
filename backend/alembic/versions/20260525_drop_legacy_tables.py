"""drop legacy tables

Revision ID: f7a1b8c2d3e4
Revises: e5af69fdead9
Create Date: 2026-05-25 05:27:31.513157
"""

from typing import Sequence, Union

from alembic import op

revision: str = "f7a1b8c2d3e4"
down_revision: Union[str, Sequence[str], None] = "e5af69fdead9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "DROP TABLE IF EXISTS "
        "messages, viewings, deals, clients, "
        "car_offer_images, car_offers, car_images, cars "
        "CASCADE"
    )


def downgrade() -> None:
    raise NotImplementedError(
        "drop_legacy_tables is forward-only; legacy schema cannot be restored"
    )
