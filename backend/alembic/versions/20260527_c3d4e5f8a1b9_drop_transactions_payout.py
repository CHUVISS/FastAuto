"""drop transactions + payout tables + listings.payout_method_id

Revision ID: c3d4e5f8a1b9
Revises: b2c3d4e5f8a1
Create Date: 2026-05-27

Pre-launch destructive cleanup of the seller-payout domain. Downgrade is
forward-only (NotImplementedError) — the tables held no production data.
"""

from sqlalchemy.engine import Inspector

from alembic import op

revision = "c3d4e5f8a1b9"
down_revision = "b2c3d4e5f8a1"
branch_labels = None
depends_on = None


def _drop_fk_if_exists(table: str, column: str) -> None:
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)
    for fk in insp.get_foreign_keys(table):
        if fk["constrained_columns"] == [column] and fk.get("name"):
            op.drop_constraint(fk["name"], table, type_="foreignkey")


def upgrade() -> None:
    bind = op.get_bind()
    insp = Inspector.from_engine(bind)

    if "payout_method_id" in {c["name"] for c in insp.get_columns("listings")}:
        _drop_fk_if_exists("listings", "payout_method_id")
        op.drop_column("listings", "payout_method_id")

    op.execute("DROP TABLE IF EXISTS transactions CASCADE")
    op.execute("DROP TABLE IF EXISTS payout_method_audit CASCADE")
    op.execute("DROP TABLE IF EXISTS payout_methods CASCADE")
    op.execute("DROP TYPE IF EXISTS transactionstatus")


def downgrade() -> None:  # noqa: D401
    raise NotImplementedError(
        "forward-only: pre-launch destructive drop of transactions + payout"
    )
