"""tickets.transaction_id -> reservation_id

Revision ID: b2c3d4e5f8a1
Revises: a1b2c3d4e5f7
Create Date: 2026-05-27

Repoints ``tickets.transaction_id`` to ``reservation_id`` (FK ->
reservations.id). Pre-launch: no data preservation required.
"""

import sqlalchemy as sa
from sqlalchemy.engine import Inspector

from alembic import op

revision = "b2c3d4e5f8a1"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def _drop_fk_if_exists(table: str, column: str) -> None:
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)
    for fk in insp.get_foreign_keys(table):
        if fk["constrained_columns"] == [column] and fk.get("name"):
            op.drop_constraint(fk["name"], table, type_="foreignkey")


def upgrade() -> None:
    _drop_fk_if_exists("tickets", "transaction_id")
    op.drop_column("tickets", "transaction_id")
    op.add_column("tickets", sa.Column("reservation_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_tickets_reservation",
        "tickets",
        "reservations",
        ["reservation_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_tickets_reservation", "tickets", type_="foreignkey")
    op.drop_column("tickets", "reservation_id")
    op.add_column("tickets", sa.Column("transaction_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_tickets_transaction",
        "tickets",
        "transactions",
        ["transaction_id"],
        ["id"],
    )
